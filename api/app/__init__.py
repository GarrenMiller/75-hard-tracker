import os

from flask import Flask, jsonify

from .db import init_db, close_db
from .errors import ApiError
from .auth.routes import auth_bp
from .goal_types.routes import goal_types_bp
from .goals.routes import goals_bp
from .plans.routes import plans_bp
from .profile.routes import profile_bp


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH", os.path.join(app.instance_path, "tracker.db")
        ),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
    )
    if config:
        app.config.update(config)

    app.teardown_appcontext(close_db)
    init_db(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(goal_types_bp, url_prefix="/api/goal-types")
    app.register_blueprint(goals_bp, url_prefix="/api/goals")
    app.register_blueprint(plans_bp, url_prefix="/api/plans")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")

    @app.errorhandler(ApiError)
    def api_error(e):
        return jsonify({"error": e.message}), e.status_code

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    return app
