# Privacy Policy — Fox-Pinterest (BlissFox Pin Manager)

**Last Updated:** June 10, 2026

## 1. Introduction

Fox-Pinterest (the "App") is a command-line tool designed to help the user manage Pinterest pins for their Etsy shop. This Privacy Policy describes what data the App collects, how it is used, and how it is protected.

## 2. Data We Collect

### 2.1 Data Stored Locally
The App stores the following data **locally on your device only**:

| Data | Purpose | Storage | Retention |
|---|---|---|---|
| Pinterest access token | Authenticate with Pinterest API | Encrypted local file (~/.fox-pinterest/token) | Until you revoke access or run `logout` |
| Configuration settings | App preferences | Plain text config file (~/.fox-pinterest/config) | Until you delete them |

### 2.2 Data We Do NOT Collect
The App does **not** collect, transmit, or store:
- Your Pinterest username or password
- Your Etsy credentials
- Any personal information about Pinterest end users
- Any analytics, usage telemetry, or crash reports
- Any data from Pinterest beyond what is necessary to perform the scheduling function

## 3. How We Use Your Data

- **Pinterest access token:** Used solely to authenticate API requests to Pinterest on your behalf.
- **Configuration settings:** Used solely to configure the App's behavior.

No data is sent to any third-party server, cloud service, or analytics platform.

## 4. Data Sharing

We **do not share, sell, or distribute** any of your data to any third party. The App operates entirely offline except for direct API calls to Pinterest.

## 5. Data Security

- Access tokens are stored in a local file with `600` permissions (readable only by you).
- The App does not log or print credentials or tokens.
- If you suspect your credentials have been compromised, revoke them immediately via your Pinterest account settings and run `fox-pinterest logout`.

## 6. Your Rights

- **Access:** All your data stored by the App is on your local machine. You can inspect it at any time.
- **Deletion:** Run `fox-pinterest logout` to delete your access token and all Pinterest authentication data.
- **Revocation:** Revoke the App's access at any time via [Pinterest App Settings](https://www.pinterest.com/settings/developer).

## 7. Children's Privacy

This App is not intended for use by individuals under 13 years of age. It is a tool used by an adult business owner to manage their own social media presence.

## 8. Changes to This Policy

We may update this Privacy Policy from time to time. Changes will be posted in this file with an updated date. Continued use of the App after changes constitutes acceptance of the updated policy.

## 9. Contact

For questions about this Privacy Policy, contact the App developer at: [ashley@coffeelogik.com](mailto:ashley@coffeelogik.com)

---

*This Privacy Policy is consistent with applicable U.S. federal and state laws, including the California Consumer Privacy Act (CCPA).*
