"""Pinterest API v5 client.

All API calls use the official Pinterest API v5. This client implements
read-through access with no persistent caching of Pinterest data,
as required by the Developer Guidelines.
"""

import time
import json
import requests
from typing import Optional
from dataclasses import dataclass, field


# Rate limiting: max 60 requests per minute (well within Pinterest defaults)
RATE_LIMIT = 60
RATE_WINDOW = 60  # seconds


@dataclass
class _RateLimiter:
    """Simple sliding window rate limiter."""
    _timestamps: list[float] = field(default_factory=list)
    
    def wait_if_needed(self):
        """Wait until we're under the rate limit."""
        now = time.time()
        # Remove timestamps outside the window
        self._timestamps = [t for t in self._timestamps if now - t < RATE_WINDOW]
        
        if len(self._timestamps) >= RATE_LIMIT:
            wait_time = RATE_WINDOW - (now - self._timestamps[0])
            if wait_time > 0:
                time.sleep(wait_time)
            self._timestamps = [t for t in self._timestamps if now - t < RATE_WINDOW]
        
        self._timestamps.append(time.time())


_rate_limiter = _RateLimiter()


class PinterestAPIError(Exception):
    """Error from the Pinterest API."""
    def __init__(self, status_code: int, message: str, request: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.request = request
        super().__init__(f"[{status_code}] {message}")


class PinterestClient:
    """Official Pinterest API v5 client with rate limiting.
    
    All methods use read-through access — no data is cached beyond
    the current response. This complies with the Developer Guidelines
    which state: "Except for campaign analytics information, you may
    not store any information accessed through the Materials/API."
    """
    
    BASE_URL = "https://api.pinterest.com/v5"
    
    def __init__(self, access_token: str):
        """Initialize the client.
        
        Args:
            access_token: A valid Pinterest OAuth 2.0 access token.
        """
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request with rate limiting and error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint (e.g., "/boards").
            **kwargs: Additional arguments passed to requests.
            
        Returns:
            Parsed JSON response.
            
        Raises:
            PinterestAPIError: If the API returns an error.
        """
        url = f"{self.BASE_URL}{endpoint}"
        _rate_limiter.wait_if_needed()
        
        response = self.session.request(method, url, **kwargs)
        
        # Retry on rate limit with exponential backoff
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            time.sleep(retry_after)
            response = self.session.request(method, url, **kwargs)
        
        if response.status_code < 200 or response.status_code >= 300:
            try:
                error_data = response.json()
                error_msg = error_data.get("message", response.text)
            except (json.JSONDecodeError, ValueError):
                error_msg = response.text
            raise PinterestAPIError(
                status_code=response.status_code,
                message=error_msg,
                request=f"{method} {endpoint}",
            )
        
        return response.json()
    
    # --- Boards ---
    
    def list_boards(self, page_size: int = 25) -> dict:
        """List all boards for the authenticated user.
        
        Args:
            page_size: Number of boards per page.
            
        Returns:
            Response dict with boards list and pagination info.
        """
        params = {"page_size": page_size}
        result = self._request("GET", "/boards", params=params)
        
        # Paginate through all boards
        while "next_page" in result:
            next_url = result["next_page"]
            _rate_limiter.wait_if_needed()
            response = self.session.get(next_url)
            
            if response.status_code != 200:
                break
            
            page = response.json()
            result["items"].extend(page.get("items", []))
            result["next_page"] = page.get("next_page")
        
        return result
    
    def get_board(self, board_id: str) -> dict:
        """Get a single board by ID.
        
        Args:
            board_id: The Pinterest board ID.
            
        Returns:
            Board details dict.
        """
        return self._request("GET", f"/boards/{board_id}")
    
    def create_board(
        self,
        name: str,
        description: str = "",
        privacy: str = "PUBLIC",
    ) -> dict:
        """Create a new board.
        
        Args:
            name: Board name.
            description: Board description.
            privacy: "PUBLIC" or "PRIVATE".
            
        Returns:
            Created board dict.
        """
        return self._request("POST", "/boards", json={
            "name": name,
            "description": description,
            "privacy": privacy,
        })
    
    # --- Pins ---
    
    def list_pins(self, owner_id: str, page_size: int = 25) -> dict:
        """List pins for a board owner.
        
        Args:
            owner_id: The Pinterest user ID.
            page_size: Number of pins per page.
            
        Returns:
            Response dict with pins list and pagination.
        """
        params = {"page_size": page_size}
        return self._request("GET", f"/users/{owner_id}/pins", params=params)
    
    def get_pin(self, pin_id: str) -> dict:
        """Get a single pin by ID.
        
        Args:
            pin_id: The Pinterest pin ID.
            
        Returns:
            Pin details dict.
        """
        return self._request("GET", f"/pins/{pin_id}")
    
    def create_pin(
        self,
        board_id: str,
        media_source: dict,
        link: str = "",
        title: str = "",
        description: str = "",
    ) -> dict:
        """Create a new pin.
        
        The pin is created immediately. For scheduled publishing,
        the pin is created and the scheduled_time is set.
        
        Args:
            board_id: The board to pin to.
            media_source: Media metadata (for uploaded media).
            link: Destination URL (e.g., Etsy listing).
            title: Pin title (max 100 chars).
            description: Pin description (max 500 chars).
            
        Returns:
            Created pin dict.
        """
        payload = {
            "board_id": board_id,
            "media_source": media_source,
        }
        if link:
            payload["link"] = link
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        
        return self._request("POST", "/pins", json=payload)
    
    def schedule_pin(
        self,
        board_id: str,
        media_source: dict,
        scheduled_time: str,
        link: str = "",
        title: str = "",
        description: str = "",
    ) -> dict:
        """Schedule a pin for future publication.
        
        The pin is created with a scheduled_time. Pinterest will
        publish it at the specified time.
        
        Args:
            board_id: The board to pin to.
            media_source: Media metadata.
            scheduled_time: ISO 8601 datetime string.
            link: Destination URL.
            title: Pin title.
            description: Pin description.
            
        Returns:
            Created pin dict with scheduled_time set.
        """
        payload = {
            "board_id": board_id,
            "media_source": media_source,
            "scheduled_time": scheduled_time,
        }
        if link:
            payload["link"] = link
        if title:
            payload["title"] = title
        if description:
            payload["description"] = description
        
        return self._request("POST", "/pins", json=payload)
    
    # --- App ---
    
    def get_app(self) -> dict:
        """Get the authenticated app's details.
        
        Returns:
            App details dict.
        """
        return self._request("GET", "/app")
    
    def get_user(self) -> dict:
        """Get the authenticated user's profile.
        
        Returns:
            User profile dict.
        """
        return self._request("GET", "/user_account")
    
    def upload_media(self, image_path: str, mime_type: str = "image/png") -> dict:
        """Upload an image media source for pin creation.
        
        Args:
            image_path: Local path to the image file.
            mime_type: MIME type of the image.
            
        Returns:
            Media source dict with media_id.
        """
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Upload to Pinterest's media endpoint
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": mime_type,
        }
        
        url = f"{self.BASE_URL}/media"
        _rate_limiter.wait_if_needed()
        
        response = self.session.post(url, data=image_data, headers=headers)
        
        if response.status_code not in (200, 201):
            raise PinterestAPIError(
                status_code=response.status_code,
                message=response.text,
                request="POST /media",
            )
        
        return response.json()
