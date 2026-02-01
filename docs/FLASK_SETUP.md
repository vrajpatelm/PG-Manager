# Flask Setup (Windows)

1. Create a virtual environment and install requirements:

   powershell
   ```powershell
   .\scripts\setup.ps1
   ```

2. Copy `.env.example` to `.env` and adjust if needed.

3. Run the app:

   powershell
   ```powershell
   .\scripts\run.ps1
   ```

4. Or use the VS Code task "Run Flask" or the debug configuration "Python: Flask (run.py)".

Test: open http://127.0.0.1:5000/ and you should see a JSON hello message.

---

## Tailwind (Tailwind CLI method)

1. Install Node dependencies (if you haven't already):

```powershell
npm install
```

2. Build the Tailwind CSS once:

```powershell
npm run build:css
```

This will generate `app/static/css/tailwind.css` which is included by `app/templates/index.html`.

3. During development, run the watcher to rebuild on change:

```powershell
npm run watch:css
```

4. Edit styles in `src/styles/input.css` or add classes directly in your HTML templates; the watcher will rebuild automatically.

5. (Optional) Use the VS Code task to run the Tailwind watcher: Tasks > Run Task > Watch Tailwind.

---

## Single-command dev workflow (`npm run dev`)

You can run both the Tailwind watcher and the Flask server with one command using the `dev` script. Before running it, make sure your Python virtual environment is active so `python` points to the venv interpreter (recommended):

```powershell
# Activate venv (example paths)
.\venv\Scripts\Activate.ps1    # or
.\.venv\Scripts\Activate.ps1

# Then in the project root run:
npm run dev
```

This runs both processes in one terminal via `concurrently`. The Tailwind watcher rebuilds CSS on file change and Flask serves your app. If you prefer separate consoles, you can still run the watch and Flask commands in different terminals.


