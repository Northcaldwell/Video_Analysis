# src/processing/routes.py
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    Response,
    flash,
)
from src.models import Project
from src.tasks import process_project
from celery.result import AsyncResult

bp = Blueprint(
    'processing',
    __name__,
    template_folder='../templates/processing'
)

@bp.route('/<int:project_id>', methods=['GET'])
def dashboard(project_id):
    """Show the processing dashboard, listing available plugins."""
    project = Project.query.get_or_404(project_id)
    plugins = current_app.config.get('AVAILABLE_PLUGINS', [])
    return render_template('processing.html', project=project, plugins=plugins)

@bp.route('/<int:project_id>/start', methods=['POST'], endpoint='start')
def start_analysis(project_id):
    """Kick off the Celery task and redirect back to dashboard."""
    selected = request.form.getlist('plugins')
    process_project.delay(project_id, selected)
    flash("Processing kicked off! Logs will stream below.")
    return redirect(url_for('processing.dashboard', project_id=project_id))

@bp.route('/<int:project_id>/events', methods=['GET'])
def events(project_id):
    """
    Server-Sent Events endpoint that streams real-time log messages
    from Redis pub/sub channel `processing:<project_id>`.
    """
    # Grab Redis & PubSub while we’re still in app context
    redis_client = current_app.extensions['redis']
    pubsub = redis_client.pubsub()
    channel = f"processing:{project_id}"
    pubsub.subscribe(channel)

    def generate():
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            data = message['data']
            text = data.decode() if isinstance(data, bytes) else str(data)
            yield f"data: {text}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@bp.route('/<int:project_id>/cancel', methods=['DELETE'])
def cancel_project(project_id):
    """Revoke a running Celery task (by `task_id` query param)."""
    task_id = request.args.get('task_id')
    celery_app = current_app.extensions['celery']
    result = AsyncResult(task_id, app=celery_app)
    result.revoke(terminate=True)
    return {'status': 'cancelled'}, 200
