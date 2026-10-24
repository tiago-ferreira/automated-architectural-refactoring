"""Composition Root do Task Manager API (Padrão MVC)."""
from flask import Flask
from flask_cors import CORS
from config.settings import Config, utc_now
from database import db
from middlewares.error_handler import register_error_handlers
from routes import category_bp, report_bp, task_bp, user_bp


def create_app() -> Flask:
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    CORS(flask_app)
    db.init_app(flask_app)

    register_error_handlers(flask_app)
    flask_app.register_blueprint(task_bp)
    flask_app.register_blueprint(user_bp)
    flask_app.register_blueprint(category_bp)
    flask_app.register_blueprint(report_bp)

    @flask_app.route("/health")
    def health():
        return {"status": "ok", "timestamp": str(utc_now())}

    @flask_app.route("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    with flask_app.app_context():
        db.create_all()

    return flask_app


app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
