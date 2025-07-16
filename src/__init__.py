import os
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from celery import Celery

from .config import Config

# Initialize extensions
db     = SQLAlchemy()
mail   = Mail()
celery = Celery(__name__)

def create_app():
    # Compute project root (one level above src/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    # Create Flask app, pointing to root-level templates/ and static/
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    app.config.from_object(Config)

    # Initialize Flask extensions
    db.init_app(app)
    mail.init_app(app)

    # Configure Celery
    celery.conf.broker_url     = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    celery.autodiscover_tasks(['src.tasks'])
    app.extensions['celery'] = celery

    # Configure Redis for SSE
    redis_url = app.config.get('REDIS_URL', app.config['CELERY_BROKER_URL'])
    client    = redis.from_url(redis_url)
    app.extensions['redis'] = client

    # Register Blueprints
    from .main.routes       import bp as main_bp
    from .processing.routes import bp as proc_bp
    from .results.routes    import bp as results_bp
    from .sessions.routes   import bp as sessions_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(proc_bp,    url_prefix='/processing')
    app.register_blueprint(results_bp, url_prefix='/results')
    app.register_blueprint(sessions_bp, url_prefix='/sessions')

    return app
