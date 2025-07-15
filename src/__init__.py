import os
import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from celery import Celery
from .config import Config
from .sessions.routes import bp as sessions_bp

# Initialize Flask extensions
db     = SQLAlchemy()
mail   = Mail()
# Create Celery without broker/backend yet
celery = Celery(__name__)

def create_app():
    # Compute project root (one level above src/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

    # Tell Flask where to find top-level templates/ and static/
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static')
    )
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    mail.init_app(app)

    # ——— Celery setup ———
    celery.conf.broker_url      = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend  = app.config['CELERY_RESULT_BACKEND']
    celery.autodiscover_tasks(['src.tasks'])
    app.extensions['celery']    = celery

    # ——— Redis setup ———
    redis_url = app.config.get('REDIS_URL', app.config['CELERY_BROKER_URL'])
    app.extensions['redis'] = redis.from_url(redis_url)

    # ——— Blueprints ———
    from .main.routes       import bp as main_bp
    from .processing.routes import bp as proc_bp
    from .results.routes    import bp as results_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(proc_bp,    url_prefix='/processing')
    app.register_blueprint(results_bp, url_prefix='/results')
    app.register_blueprint(sessions_bp, url_prefix='/sessions')

    return app