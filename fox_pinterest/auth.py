"""OAuth 2.0 + PKCE flow for Pinterest API authentication.

This module handles the complete OAuth 2.0 authorization code flow with PKCE
for the Pinterest API. It never stores or handles user passwords.
"""

import os
import secrets
import hashlib
import base64
import webbrowser
import http.server
import threading
import json
import time
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet


# Pinterest OAuth endpoints
PINTEREST_AUTH_URL = "https://www.pinterest.com/oauth/"
PINTEREST_TOKEN_URL = "https://www.pinterest.com/oauth/token"
PINTEREST_API_BASE = "https://api.pinterest.com/v5"

# Configuration
CONFIG_DIR = Path.home() / ".fox-pinterest"
TOKEN_FILE = CONFIG_DIR / "token.enc"
CONFIG_FILE = CONFIG_DIR / "config.json"


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a code verifier and code challenge for PKCE.
    
    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    code_verifier = secrets.token_urlsafe(43)
    # S256 challenge: base64-url-encode(SHA256(verifier))
    sha256_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def encrypt_token(token: str, secret_key: Optional[str] = None) -> bytes:
    """Encrypt and return a Pinterest access token for local storage.
    
    Args:
        token: The raw access token string.
        secret_key: Optional encryption key. If None, generates one.
        
    Returns:
        Encrypted token bytes.
    """
    if secret_key is None:
        secret_key = Fernet.generate_key().decode("ascii")
    f = Fernet(secret_key.encode("ascii"))
    return f.encrypt(token.encode("ascii"))


def decrypt_token(encrypted_token: bytes, secret_key: str) -> str:
    """Decrypt a stored Pinterest access token.
    
    Args:
        encrypted_token: Encrypted token bytes.
        secret_key: The Fernet encryption key.
        
    Returns:
        Decrypted token string.
    """
    f = Fernet(secret_key.encode("ascii"))
    return f.decrypt(encrypted_token).decode("ascii")


def load_encryption_key() -> str:
    """Load or generate a local encryption key for storing tokens.
    
    The key is stored in the config file alongside the encrypted token.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        if "encryption_key" in config:
            return config["encryption_key"]
    
    # Generate new key
    key = Fernet.generate_key().decode("ascii")
    config = {"encryption_key": key}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)
    return key


def get_auth_url(app_id: str, redirect_uri: str) -> tuple[str, str]:
    """Generate the Pinterest OAuth authorization URL and PKCE pair.
    
    Args:
        app_id: The Pinterest app's API key.
        redirect_uri: The configured redirect URI.
        
    Returns:
        Tuple of (authorization_url, code_verifier)
    """
    code_verifier, code_challenge = generate_pkce_pair()
    
    params = {
        "response_type": "code",
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "boards:read,pins:read,pins:write,apps:read",
        "state": secrets.token_urlsafe(16),
    }
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"{PINTEREST_AUTH_URL}?{query_string}"
    
    return auth_url, code_verifier


class CallbackServer(http.server.BaseHTTPRequestHandler):
    """Simple HTTP server to receive the OAuth callback."""
    
    code: Optional[str] = None
    error: Optional[str] = None
    
    def do_GET(self):
        """Handle the OAuth callback."""
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if "error" in params:
            CallbackServer.error = params["error"][0]
            self._send_response(400, "Authorization failed")
            return
        
        if "code" in params:
            CallbackServer.code = params["code"][0]
            self._send_response(200, "Authorization successful! You can close this tab.")
            return
        
        self._send_response(400, "No code or error in response")
    
    def _send_response(self, status: int, message: str):
        """Send an HTTP response."""
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def exchange_code_for_token(
    app_id: str,
    app_secret: str,
    code: str,
    redirect_uri: str,
) -> str:
    """Exchange an authorization code for an access token.
    
    Args:
        app_id: The Pinterest app's API key.
        app_secret: The Pinterest app's API secret.
        code: The authorization code from the callback.
        redirect_uri: The configured redirect URI.
        
    Returns:
        Access token string.
    """
    import requests
    
    response = requests.post(
        PINTEREST_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": app_id,
            "client_secret": app_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    response.raise_for_status()
    
    token_data = response.json()
    return token_data["access_token"]


def login(
    app_id: str,
    app_secret: str,
    redirect_uri: str = "https://localhost:8080/callback",
) -> str:
    """Complete the OAuth login flow.
    
    Opens a browser for Pinterest authorization, waits for the callback,
    exchanges the code for a token, and stores it encrypted locally.
    
    Args:
        app_id: The Pinterest app's API key.
        app_secret: The Pinterest app's API secret.
        redirect_uri: The configured redirect URI (default: localhost).
        
    Returns:
        The access token string.
    """
    # Start callback server
    server = http.server.HTTPServer(("127.0.0.1", 8080), CallbackServer)
    callback_thread = threading.Thread(target=server.serve_forever, daemon=True)
    callback_thread.start()
    
    try:
        # Generate auth URL and open browser
        auth_url, _ = get_auth_url(app_id, redirect_uri)
        print(f"Opening Pinterest authorization in your browser...")
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("Waiting for authorization...")
        start_time = time.time()
        while CallbackServer.code is None and CallbackServer.error is None:
            if time.time() - start_time > 300:  # 5 minute timeout
                raise TimeoutError(
                    "Authorization timed out. Please try again."
                )
            server.handle_request()
        
        if CallbackServer.error:
            raise RuntimeError(f"Authorization failed: {CallbackServer.error}")
        
        code = CallbackServer.code  # type: ignore[unreachable]
        assert code is not None, "Expected an authorization code"
        
        # Exchange code for token
        print("Exchanging authorization code for token...")
        token = exchange_code_for_token(app_id, app_secret, code, redirect_uri)
        
        # Store token encrypted
        secret_key = load_encryption_key()
        encrypted = encrypt_token(token, secret_key)
        
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            f.write(encrypted)
        os.chmod(TOKEN_FILE, 0o600)
        
        print("Successfully authenticated with Pinterest.")
        return token
        
    finally:
        server.shutdown()


def get_stored_token() -> Optional[str]:
    """Load and decrypt the stored access token.
    
    Returns:
        The access token string, or None if no token is stored.
    """
    if not TOKEN_FILE.exists():
        return None
    
    try:
        secret_key = load_encryption_key()
        with open(TOKEN_FILE, "rb") as f:
            encrypted = f.read()
        return decrypt_token(encrypted, secret_key)
    except Exception:
        return None


def logout():
    """Remove stored credentials."""
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
    print("Logged out. Credentials removed.")
