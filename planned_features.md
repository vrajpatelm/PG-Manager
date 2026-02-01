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

## 3. Data & Management
### 📂 Document Vault
- **Goal**: Secure storage for important agreements and IDs.
- **Features**:
    - **Owner**: Upload Rental Templates, Property Docs.
    - **Tenant**: Upload ID Proofs (Aadhar/PAN).
    - **Shared**: View signed Rental Agreement.

### 📝 Visitor Log
- **Goal**: Track guests entering/exiting the PG.
- **Features**: Digital entry for visitors (Name, Whom to visit, Time In/Out).
