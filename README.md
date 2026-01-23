# PG-Manager 🏠

**PG-Manager** is a modern, comprehensive Property Management System (PMS) designed for Hostel and Paying Guest (PG) owners. It simplifies the chaos of managing tenants, rooms, payments, and complaints into a single, beautiful dashboard.

## 🚀 Key Features

*   **Role-Based Access**: Secure login/signup for Owners and Tenants.
*   **Tenant Management**: Onboard new tenants, track lease dates, and manage active/past residents.
*   **Smart Room Allocation**: Visual bed management with capacity tracking.
*   **Finance Dashboard**: 
    *   Track Rent Payments (Cash, UPI, Bank).
    *   Record Expenses (Utilities, Maintenance, Salaries).
    *   Real-time **Net Profit** calculation.
*   **Complaint System**: Tenant-raised issues with priority tracking (High/Medium/Low) and resolution workflow.
*   **Tenant Portal**:
    *   **Dashboard**: View rent due, payment history, and lease details.
    *   **Online Payments**: Pay rent via UPI and submit transaction details for verification.
    *   **Dark Mode**: Toggle between light and dark themes.
*   **Properties & Rooms**: Manage multiple buildings and configure room capacity/pricing.
*   **Responsive Design**: Built with Tailwind CSS for a seamless mobile and desktop experience.

## 🛠️ Tech Stack

*   **Backend**: Python, Flask, Jinja2
*   **Database**: PostgreSQL
*   **Frontend**: HTML5, Tailwind CSS, JavaScript
*   **Authentication**: Werkzeug Security

## 📚 Documentation

*   **[Setup Guide](SETUP.md)**: Step-by-step instructions to install and run the project locally.
*   **[Contributing](CONTRIBUTING.md)**: Guidelines for code contributions and pull requests.

## ⚡ Quick Start

### Windows (One-Command)
We provide a helper script to set up everything (Python venv, dependencies, database) in one go:
```powershell
.\setup.ps1
```
Then, start the server:
```bash
npm run dev
```

### Manual Setup
1.  **Clone** the repo.
2.  **Setup** database and environment variables (Detailed in [SETUP.md](docs/SETUP.md)).
3.  **Run**:
    ```bash
    npm run dev
    ```

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
