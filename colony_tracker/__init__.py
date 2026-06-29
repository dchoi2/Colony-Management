"""Colony Management tracker - application factory.

This package wires together the database and the web routes. The
``create_app`` function builds the Flask application and is called by
``run.py``.
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# A single shared database handle used across the whole app.
db = SQLAlchemy()


def create_app(database_uri=None):
    """Create and configure the Flask application.

    Args:
        database_uri: Optional SQLAlchemy database URL. Defaults to a
            local SQLite file named ``colony.db`` in the project folder.
    """
    app = Flask(__name__)

    # Where the SQLite database file lives (project root, one level up).
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_uri = "sqlite:///" + os.path.join(project_root, "colony.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri or default_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Used to keep flash messages secure; override via env var in production.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")

    db.init_app(app)

    # Import models so SQLAlchemy knows about the tables, then create them.
    from . import models  # noqa: F401

    with app.app_context():
        db.create_all()

    # Register all the page routes.
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
