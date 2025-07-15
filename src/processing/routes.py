from flask import Blueprint, render_template, current_app, request, jsonify, abort, stream_with_context
from src.models import Project, File
from src.tasks import process_project
from celery.result import AsyncResult
from celery import Celery
import time

bp = Blueprint(
    'processing',
    __name__,
    template_folder='templates',
    url_prefix='/processing'
)

@bp.route('/<int:project_id>', methods=['GET'])
def dashboard(project_id):
    project = Project.query.get_or_404(project_id)
    files = File.query.filter_by(project_id=project_id).all()
    plugins = current_app.config.get('AVAILABLE_PLUGINS', [])
    return render_template(
        'processing.html',
        project=project,
        files=files,
        plugins=plugins
    )

@bp.route('/<int:project_id>/start', methods=['POST'])
def start_analysis(project_id):
    project = Project.query.get_or_404(project_id)
    selected = request.form.getlist('plugins')
    if not selected:
        return jsonify({'error': 'No plugins selected'}), 400

    task = process_project.delay(project_id, selected)
    return jsonify({'task_id': task.id}), 202

@bp.route('/<int:project_id>/cancel', methods=['DELETE'])
def cancel_project(project_id):
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'task_id required'}), 400
    celery = Celery(current_app.import_name)
    result = AsyncResult(task_id, app=celery)
    result.revoke(terminate=True)
    project = Project.query.get_or_404(project_id)
    from src import db
    project.status = 'cancelled'
    db.session.commit()
    return ('', 204)

@bp.route('/<int:project_id>/events', methods=['GET'])
def events(project_id):
    redis_client = current_app.extensions.get('redis')
    if redis_client is None:
        abort(500, description="Redis client not configured")
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f'project_{project_id}')

    @stream_with_context
    def generate():
        for message in pubsub.listen():
            data = message.get('data')
            if isinstance(data, (bytes, bytearray)):
                text = data.decode('utf-8')
                yield f"data: {text}\n\n"
                if text.strip().lower() == 'complete':
                    break

    return current_app.response_class(
        generate(),
        mimetype='text/event-stream'
    )