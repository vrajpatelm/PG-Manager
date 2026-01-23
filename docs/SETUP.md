# Setup Guide for PG-Manager 🛠️

This guide covers the complete installation and configuration process for setting up PG-Manager locally.

## Prerequisites

-   **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
-   **PostgreSQL 14+**: [Download PostgreSQL](https://www.postgresql.org/download/)
-   **Node.js 16+**: [Download Node.js](https://nodejs.org/) (for Tailwind CSS)
-   **Git**: [Download Git](https://git-scm.com/)

---

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd PG-Manager
```

## 2. Environment Configuration

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    *(On Windows PowerShell: `Copy-Item .env.example .env`)*

2.  Open `.env` and configure your database credentials:
    ```ini
    DB_NAME=pg_manager
    DB_USER=postgres
    DB_PASSWORD=your_password
    DB_HOST=localhost
    DB_PORT=5432
    SECRET_KEY=your_secret_key_here
    ```

---

## 3. Database Setup 🗄️

PG-Manager uses a schema migration approach. You need to run the SQL scripts in the `database_schemas/` folder in order.

1.  **Create the Database**:
    Open your terminal or pgAdmin and run:
    ```sql
    CREATE DATABASE pg_manager;
    ```

2.  **Apply Schemas**:
    Run the following command to execute all schema files in order. 
    
    **Option A: Using Python Helper (Recommended)**
    We have a helper script coming soon, but for now, you can use the command line.

    **Option B: Using psql (Command Line)**
    ```bash
    # Linux/Mac
    psql -U postgres -d pg_manager -f database_schemas/01_init_schema.sql
    psql -U postgres -d pg_manager -f database_schemas/02_add_rent_columns.sql
    psql -U postgres -d pg_manager -f database_schemas/03_add_properties_rooms.sql
    psql -U postgres -d pg_manager -f database_schemas/04_add_payments.sql
    psql -U postgres -d pg_manager -f database_schemas/05_add_complaints.sql
    psql -U postgres -d pg_manager -f database_schemas/06_add_expenses.sql
    psql -U postgres -d pg_manager -f database_schemas/07_update_settings_schema.sql
    ```

    **Option C: Using pgAdmin / GUI**
    Open the Query Tool for `pg_manager` database and Copy-Paste the content of each file in `database_schemas/` sequentially (01 to 07) and execute them.

---

## 4. Backend Setup (Python)

1.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    ```

2.  **Activate Virtual Environment**:
    -   **Windows (PowerShell)**: `.\venv\Scripts\Activate`
    -   **Mac/Linux**: `source venv/bin/activate`

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 5. Frontend Setup (Tailwind CSS)

1.  **Install Node Modules**:
    ```bash
    npm install
    ```

2.  **Build CSS**:
    ```bash
    npm run build:css
    ```

---

## 6. Running the Application 🚀

You can run both the Flask backend and Tailwind watcher with a single command:

```bash
npm run dev
```

-   Access the app at: `http://127.0.0.1:5000`
-   Login with the test user or create a new account.

---

## Troubleshooting

-   **Database Connection Error**: Double-check your `.env` file credentials and ensure PostgreSQL service is running.
-   **CSS Not Loading**: Run `npm run build:css` again to ensure Tailwind generated the output file.
