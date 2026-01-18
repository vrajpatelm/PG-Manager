from flask import Flask


def create_app():
    """Application factory"""
    app = Flask(__name__)
    import os
    app.secret_key = os.environ.get('SECRET_KEY') or 'dev_secret_key_change_in_production'

    # Register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
