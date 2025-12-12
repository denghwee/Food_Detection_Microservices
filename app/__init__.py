from flask import Flask

from .config import Config
from .routes import register_routes

def create_app(config_object=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load config
    app.config.from_object(config_object)

    register_routes(app)
    return app