# API Documentation 📡

This document describes the key routes and API endpoints for the PG-Manager application.

## Authentication

### `POST /login`
*   **Description**: Authenticates a user (Owner or Tenant).
*   **Form Data**: `email`, `password`.
*   **Response**: Redirects to `/owner/dashboard` or `/tenant/dashboard` on success.

### `POST /signup`
*   **Description**: Registers a new user.
*   **Form Data**: `full_name`, `email`, `phone`, `password`, `role` (OWNER/TENANT).
*   **Response**: Redirects to `/login`.

---

## Owner Endpoints

### `GET /owner/dashboard`
*   **Description**: Main dashboard view with financial summaries, occupancy stats, and pending actions.
*   **Response**: HTML Page.

### `POST /owner/tenants/add`
*   **Description**: onboards a new tenant.
*   **Form Data**: `full_name`, `email`, `phone`, `room_id`, `rent_amount`, `security_deposit`, `move_in_date`.
*   **Response**: Redirects to `/owner/tenants`.

### `POST /owner/payment/approve/<payment_id>`
*   **Description**: Verifies a tenant's rent payment.
*   **Response**: Redirects to the referring page (Finance or Dashboard).

### `POST /owner/settings/update`
*   **Description**: Updates owner profile, UPI details, and application preferences.
*   **Form Data**: `upi_id`, `bank_account`, `utility_rate`, `wifi_ssid`, `notification_prefs` (JSON).
*   **Response**: Redirects to `/owner/settings` with a flash message.

---

## Tenant Endpoints

### `GET /tenant/dashboard`
*   **Description**: Tenant's main view showing rent due, lease info, and payment history.
*   **Response**: HTML Page.

### `POST /tenant/pay`
*   **Description**: Submits a manual rent payment record.
*   **Form Data**: `amount`, `transaction_id`.
*   **Response**: Redirects to `/tenant/dashboard`.

### `POST /tenant/complaint`
*   **Description**: Logs a new complaint.
*   **Form Data**: `title`, `description`, `priority`.
*   **Response**: Redirects to `/tenant/dashboard`.
