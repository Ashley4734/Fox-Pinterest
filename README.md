# Fox-Pinterest

A Pinterest API client for BlissFox Studio — a Pin scheduler and content management tool for Etsy merchants.

## Purpose

This application helps small e-commerce merchants (specifically [BlissFox Studio](https://www.etsy.com/shop/BlissFoxStudio)) schedule and manage Pinterest pins that link to Etsy product listings. It is designed as a **content marketing tool** in full compliance with [Pinterest Developer Guidelines](https://policy.pinterest.com/en/developer-guidelines) and [Pinterest Developer and API Terms of Service](https://developers.pinterest.com/terms/).

## Features

- **OAuth 2.0 login** — Uses Pinterest's official OAuth flow with PKCE; never stores or handles user passwords.
- **Board management** — Lists boards, selects target boards for new pins.
- **Pin scheduling** — Schedule pins with date/time; the user must approve each pin before it's published.
- **Etsy link management** — Associate pins with Etsy product URLs.
- **Pin preview** — Show pin metadata before publishing.
- **Rate-limit awareness** — Built-in rate limiting to respect Pinterest API quotas.

## Architecture

```
Fox-Pinterest/
├── fox_pinterest/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── auth.py             # OAuth 2.0 + PKCE flow
│   ├── api.py              # Pinterest API client (v5)
│   ├── scheduler.py        # Pin scheduling logic
│   └── compliance.py       # Compliance checks & disclosures
├── docs/
│   ├── compliance.md       # Compliance statement
│   └── privacy-policy.md   # Privacy policy
├── .env.example            # Template for environment variables
├── .gitignore
├── pyproject.toml          # Project config + dependencies
├── README.md
└── LICENSE
```

## Getting Started

### 1. Pinterest Developer App Registration

Before using this tool, register a Pinterest Developer App at [developers.pinterest.com/apps](https://developers.pinterest.com/apps):

- **App Name:** BlissFox Pin Manager
- **Description:** Internal content marketing tool for scheduling and managing Pinterest pins that link to my Etsy shop. Helps optimize product visibility on Pinterest for my coloring book catalog.
- **Website:** https://www.etsy.com/shop/BlissFoxStudio
- **Redirect URI:** `https://localhost:8080/callback`
- **Scopes Requested:** `boards:read`, `pins:read`, `pins:write`, `apps:read`
- **Category:** Content Marketing Tool

### 2. Configuration

```bash
cd Fox-Pinterest
cp .env.example .env
# Edit .env with your Pinterest API credentials
```

Required environment variables:
- `PINTEREST_APP_ID` — Your Pinterest app's API key
- `PINTEREST_APP_SECRET` — Your Pinterest app's API secret

### 3. Install

```bash
pip install -e .
```

### 4. Authenticate

```bash
python -m fox_pinterest.cli login
```

This opens a browser window for Pinterest OAuth consent. After consent, the access token is stored locally (encrypted) for future sessions.

### 5. Use

```bash
# List boards
python -m fox_pinterest.cli boards

# Schedule a pin
python -m fox_pinterest.cli schedule --image path/to/image.png --title "My Pin" --board "Coloring Books for Adults" --link "https://www.etsy.com/listing/XXXX"

# List scheduled pins
python -m fox_pinterest.cli list-scheduled

# Approve a scheduled pin
python -m fox_pinterest.cli approve --pin-id XXXX
```

## Compliance

This app is designed to comply with:
- Pinterest Developer Guidelines
- Pinterest Developer and API Terms of Service
- Pinterest Community Guidelines
- Pinterest Brand Guidelines
- GDPR and CCPA (for applicable users)

See [docs/compliance.md](docs/compliance.md) for a full compliance statement.

## Attribution

This application uses the Pinterest API but is not endorsed or certified by Pinterest, Inc.

> "Pinterest" is a trademark of Pinterest, Inc. This application is not affiliated with, endorsed by, or sponsored by Pinterest, Inc.

## License

MIT License — see [LICENSE](LICENSE).

## Disclaimer

This tool is intended for use by the BlissFox Studio owner only. It is not a commercial product and is not offered to third parties. API credentials must never be shared or committed to version control.
