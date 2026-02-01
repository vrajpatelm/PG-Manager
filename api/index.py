from app import create_app

# Vercel looks for 'app' variable in the file
app = create_app()

# This is for Vercel's serverless environment
if __name__ == "__main__":
    app.run()
