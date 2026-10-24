"""Composition Root da API de E-commerce (Padrão MVC)."""
from flask import Flask
from flask_cors import CORS
from config.settings import Config, close_db, init_db, logger
from middlewares.error_handler import register_error_handlers
from views.routes import register_routes


def create_app() -> Flask:
    flask_app = Flask(__name__)
    flask_app.config["SECRET_KEY"] = Config.SECRET_KEY
    flask_app.config["DEBUG"] = Config.DEBUG

    CORS(flask_app)
    flask_app.teardown_appcontext(close_db)

    register_error_handlers(flask_app)
    register_routes(flask_app)
    init_db()

    return flask_app


app = create_app()

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%d", Config.HOST, Config.PORT)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
