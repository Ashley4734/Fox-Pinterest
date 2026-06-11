# Compliance Statement — Fox-Pinterest (BlissFox Pin Manager)

## 1. App Classification

**Category:** Content Marketing Tool / Pin Scheduler for Etsy Merchants

This application is a single-user content marketing tool designed to help the owner of BlissFox Studio (a small Etsy shop selling digital coloring book products) schedule and manage Pinterest pins that link to Etsy product listings.

## 2. Acceptable Use Alignment

Per [Pinterest Developer Guidelines](https://policy.pinterest.com/en/developer-guidelines), this app falls under these **acceptable uses**:

| Guideline Section | App Feature | Compliance |
|---|---|---|
| Content marketing tools (Pin schedulers) | Users schedule pins for future publication | ✅ Compliant |
| Feed management tools (optimize product listings) | Pins link to Etsy product listings with metadata | ✅ Compliant |
| Merchant platforms (ecommerce stores) | Connects Etsy shop products to Pinterest | ✅ Compliant |

## 3. Prohibited Use Avoidance

Per [Pinterest Developer Guidelines](https://policy.pinterest.com/en/developer-guidelines) "What not to do" section:

| Prohibition | How This App Avoids It |
|---|---|
| Violating Pinterest policies | App is designed to enforce compliance, not circumvent it |
| Actions without user knowledge/consent | **Every pin requires explicit user approval** before publishing |
| Automatic actions without individual consideration | Users must select each pin's image, title, board, and link individually |
| Scraping or data extraction | App uses only the official Pinterest API with proper OAuth tokens |
| Misrepresenting relationship with Pinterest | Clear attribution text in README and app output |
| Using Pinterest data for ad targeting outside Pinterest | App only schedules pins to Pinterest; no ad data extraction |
| Combining Pinterest data with other data | App treats Pinterest data as Pinterest-only; no cross-merging |
| Selling/sharing API data | Credentials stored locally; data never shared |
| Apps for children under 13 | Coloring books are marketed to all ages; the app itself is a tool, not a consumer-facing app |
| Incentivizing engagement | No gamification or engagement incentives |
| Testing rate limits without authorization | App includes built-in rate limiting (max 60 requests/minute) |

## 4. Data Handling

### Data Access
- Pinterest data is accessed **only through the official API** using OAuth 2.0 access tokens
- **No data is stored persistently** (except the user's own access token encrypted locally)
- All Pinterest data is accessed on-demand (read-through) as required by the Developer Guidelines
- The app does not cache pin content, board data, or user information beyond the access token

### Data Privacy
- The app does not collect any end-user personal information from Pinterest
- Access tokens are stored locally encrypted on the user's machine only
- No analytics, tracking, or telemetry is collected
- No cookies or device-level storage

### Compliance with Terms of Service
- Per Section 4 (Data Privacy) of Pinterest Developer/API Terms:
  - ✅ Industry-standard measures for credential protection (local file with restrictive permissions 600)
  - ✅ No Pinterest data stored beyond API session
  - ✅ Compliant with applicable privacy laws (GDPR, CCPA)
  - ✅ Privacy policy available at `docs/privacy-policy.md`

## 5. User Consent & Authorization

- The app uses **official Pinterest OAuth 2.0 flow with PKCE**
- Users must explicitly authorize the app via the Pinterest consent screen
- The app does not collect passwords, session cookies, or credentials
- Users can revoke access at any time via Pinterest account settings
- Each scheduled pin requires **explicit user approval** before publication

## 6. Rate Limiting

- Built-in rate limiter: **60 requests per minute** (well within Pinterest's default limits)
- Exponential backoff on 429 (Too Many Requests) responses
- No authorization to test Pinterest rate limits or abuse prevention systems

## 7. Brand & Publicity Compliance

- The app does not issue any press releases or public statements about Pinterest
- The app does not use Pinterest's trademarks in a misleading way
- Clear attribution text states the app is not endorsed by Pinterest
- No embellishment of the relationship between the app and Pinterest
- Brand usage follows Pinterest Brand Guidelines

## 8. Scope Justification

| Requested Scope | Justification |
|---|---|
| `boards:read` | List available boards to select where pins should be published |
| `pins:read` | View existing pins and scheduled pins for management |
| `pins:write` | Create scheduled pins that link to Etsy listings |
| `apps:read` | Verify app configuration and permissions |

**No sensitive scopes are requested.** No access to user email, profile data, ads data, or analytics data is needed.

## 9. App Review Submission Summary

> **BlissFox Pin Manager** is a content marketing tool for the owner of BlissFox Studio, a small Etsy shop selling digital coloring book products. The tool allows the owner to schedule Pinterest pins that link to Etsy product listings. Each pin is individually selected and approved by the owner before publication — there is no bulk or automated publishing. The app uses Pinterest's official OAuth 2.0 API, stores no Pinterest data beyond the local access token, and respects Pinterest rate limits. It is designed for single-user, internal use only and is not a commercial product.

## 10. Termination & Wind-Down

Upon termination of API access:
- All stored access tokens will be deleted immediately
- No Pinterest data has been stored for wind-down (per guideline: do not store API data)
- The app will cease all API calls upon receiving a 401 Unauthorized response

---

*Last updated: June 10, 2026*
