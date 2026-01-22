# Contributing to PG-Manager 🤝

Thank you for your interest in contributing! We welcome pull requests from everyone.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally.
3.  **Follow the [Setup Guide](SETUP.md)** to get the project running locally.

## Development Workflow

1.  **Create a Branch**:
    ```bash
    git checkout -b feature/amazing-feature
    ```
2.  **Make Changes**: Write your code and ensure it follows the project structure.
3.  **Test**: Verified that your changes work as expected.
4.  **Commit**: Use clear and descriptive commit messages.
    ```bash
    git commit -m "feat: add amazing feature"
    ```
5.  **Push**:
    ```bash
    git push origin feature/amazing-feature
    ```
6.  **Open a Pull Request**: Submit your PR to the `main` branch of the original repository.

## Project Structure

*   `app/`: Main Flask application.
    *   `routes.py`: Backend logic and API endpoints.
    *   `templates/`: HTML files (Jinja2).
    *   `static/`: CSS (Tailwind) and JS.
*   `database_schemas/`: SQL migration files (01 to 06).
*   `tests/`: (Future) Test suite.

## Code Style

*   **Python**: Follow PEP 8 guidelines.
*   **HTML/CSS**: Keep Tailwind classes organized (use `@apply` in `custom.css` only for highly repeated patterns).