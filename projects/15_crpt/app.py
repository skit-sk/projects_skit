"""Flask приложение — точка входа.

Запуск: python app.py [port]
Порт по умолчанию: 5000 (из env PORT или аргумента командной строки)
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv
from crpt.web.routes import web_bp

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(web_bp, url_prefix="/crpt")

    @app.route("/")
    def health():
        return "CRPT API Explorer → <a href='/crpt'>/crpt</a>"

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
