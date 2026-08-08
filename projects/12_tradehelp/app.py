"""TradeHelp — Flask app."""
from flask import Flask
import config


def create_app():
    app = Flask(
        __name__,
        template_folder=str(config.TEMPLATES),
        static_folder=str(config.STATIC),
    )
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    app.config['JSON_AS_ASCII'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    from routes.main import bp as main_bp
    from routes.learning import bp as learning_bp
    from routes.viz import bp as viz_bp
    from routes.tv import bp as tv_bp
    from routes.live import bp as live_bp
    from routes.tools import bp as tools_bp
    from routes.api import bp as api_bp
    from routes.terminal import bp as terminal_bp
    from routes.references import bp as references_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(learning_bp, url_prefix='/learn')
    app.register_blueprint(viz_bp, url_prefix='/viz')
    app.register_blueprint(tv_bp, url_prefix='/tv')
    app.register_blueprint(live_bp, url_prefix='/live')
    app.register_blueprint(tools_bp, url_prefix='/tools')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(terminal_bp)
    app.register_blueprint(references_bp)

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {
            'now': datetime.utcnow(),
            'ticker_symbols': config.TICKER_SYMBOLS,
        }

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('error.html', code=404, message='Страница не найдена'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('error.html', code=500, message='Внутренняя ошибка'), 500

    return app


if __name__ == '__main__':
    app = create_app()
    print(f"TradeHelp → http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
