# Planned Features Roadmap

## 1. Authentication & Security (Current Focus)
### ✅ OTP Verification for Signup
- **Goal**: Verify email ownership before creating accounts.
- **Flow**: User enters details -> System sends OTP to email -> User enters OTP -> Account Created.
- **Status**: *Completed*

### ✅ Password Reset Flow
- **Goal**: Allow users to recover lost passwords via email.
- **Implementation**: "Forgot Password" link -> Email with unique link/token -> New Password form.
- **Status**: *Completed*

### ✅ Security Decorators
- **Goal**: Centralize role-based access control.
- **Implementation**: Created `@login_required` and `@role_required(role)` decorators in `app/utils/decorators.py` and refactored all Owner/Tenant routes to use them.
- **Status**: *Completed*

## 2. Communication Features
### 📢 Digital Notice Board
- **Goal**: Allow Owners to broadcast announcements to all Tenants.
- **Features**: 
    - Owner Dashboard: "Post Notice" (Title, Body, Priority).
    - Tenant Dashboard: "Notices" widget with "New" badges.

## 3. Data & Management (Refined)
### �️ Asset & Inventory Management
- **Goal**: Track property assets and their health (Furniture, ACs, Geysers).
- **Features**:
    - **Inventory List**: Track items per room (e.g., Room 101: 2 Beds, 1 Study Table).
    - **Maintenance Log**: Record service dates (e.g., AC servicing history).
    - **Repair Tracking**: Link repairs to specific assets for cost analysis.

### 📊 Advanced Financial Analytics
- **Goal**: Deeper business insights for property owners.
- **Features**:
    - **Revenue Trends**: Monthly/Quarterly profit charts and predictive income.
    - **Late Fee Engine**: Automated calculation of penalties for overdue rent.
    - **Digital Receipts**: One-click PDF generation for tenant rent receipts.

## 4. Communication & Automation (Improvements)
### ⚡ Automated Reminders
- **Goal**: Reduce manual effort in rent collection.
- **Features**:
    - **One-Click Notify**: Send rent reminders via Email/WhatsApp from the Tenant List.
    - **Auto-Onboarding**: Send a digital "Welcome Kit" (WiFi, Rules) immediately upon marking a tenant as ACTIVE.

### 🔧 Maintenance Solutions
- **Goal**: Integrated complaint and cost management.
- **Features**:
    - **Technician Directory**: Save local contacts for plumbers, electricians, etc.
    - **Expense Linkage**: Automatically link complaint resolution costs to the Finance module.
