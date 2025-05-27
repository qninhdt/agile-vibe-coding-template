# User Stories for Notepot

This document lists the user stories. Each story describes a specific piece of functionality from an end-user perspective.

---

## US-001: User Registration

> - **As a** new visitor
> - **I want to** create an account using my email/username and a password
> - **So that** I can log in with my email/username and password.

- **Acceptance Criteria:**
  - AC1: User can enter an email/username.
  - AC2: User can enter a password and a confirmation password.
  - AC3: System validates email/username format.
  - AC4: System checks if email/username is already registered.
  - AC5: Passwords must match and meet complexity requirements.
  - AC6: Upon successful registration, the user is logged in and redirected to their dashboard.
  - AC7: An error message is shown for any validation failure.
- **Related Epic(s):** [EPIC-001: User Account Management](epics.md#epic-001-user-account-management)

---

## US-002: User Login

> - **As an** existing user
> - **I want to** log in with my email/username and password
> - **So that** I can access the application.

- **Acceptance Criteria:**
  - AC1: User can enter an email/username.
  - AC2: User can enter a password.
  - AC3: System verifies email/username and password.
  - AC4: Upon successful login, the user is redirected to their dashboard.
  - AC5: An error message is shown for any validation failure.
  - AC6: Ban the IP address after X failed attempts.
- **Related Epic(s):** [EPIC-001: User Account Management](epics.md#epic-001-user-account-management)

---

## US-003: User Login with Third-Party Authentication

> - **As an** existing user
> - **I want to** log in with my third-party authentication account
> - **So that** I can access the application.

- **Acceptance Criteria:**

  - AC1: User can click on the Google, Github, etc. login button.
  - AC2: User is redirected to the login page.
  - AC3: User can enter their credentials.
  - AC4: Upon successful login, the user is redirected to their dashboard.

- **Related Epic(s):** [EPIC-001: User Account Management](epics.md#epic-001-user-account-management)

---

## US-004: User Logout From Current Device

> - **As an** existing user
> - **I want to** log out of my account
> - **So that** I can secure my account.

- **Acceptance Criteria:**

  - AC1: User can click on the logout button.
  - AC2: User is redirected to the login page.
  - AC3: User is logged out of their account.

- **Related Epic(s):** [EPIC-001: User Account Management](epics.md#epic-001-user-account-management)

---

## US-005: User Device Management

> - **As an** existing user
> - **I want to** manage my logged in devices
> - **So that** I can secure my account.

- **Acceptance Criteria:**

  - AC1: User can see a list of devices.
  - AC2: User can click on a device to see the device details.
  - AC3: User can click on a device to logout from the device.
  - AC4: User can click a button to logout from all devices.
  - AC5: User can see information about the device (device name, device type, device location, device last activity time).

- **Related Epic(s):** [EPIC-001: User Account Management](epics.md#epic-001-user-account-management)

---
