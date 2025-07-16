# src/processing/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, current_app, Response
from src import db
from src.models import Project
from src.tasks import process_project
import json

bp = Blueprint(
    'processing',
    __name__,
    template_folder='../templates/processing'
)

@bp.route('/<int:project_id>', methods=['GET'])
def dashboard(project_id):
    project = Project.query.get_or_404(project_id)
    # Retrieve available plugins from config
    plugins = current_app.config.get('AVAILABLE_PLUGINS', [])
    return render_template('processing.html', project=project, plugins=plugins)

@bp.route('/<int:project_id>/start', methods=['POST'])
def start_analysis(project_id):
    selected = request.form.getlist('plugins')
    # fire-and-forget
    process_project.delay(project_id, selected)

    flash("Processing kicked off! Logs will stream below.")
    return redirect(url_for('processing.dashboard', project_id=project_id))

@bp.route('/<int:project_id>/events', methods=['GET'])
def events(project_id):
    # Server-Sent Events endpoint
    def generate():
        redis_client = current_app.extensions['redis']
        pubsub = redis_client.pubsub()
        channel = f"processing:{project_id}"
        pubsub.subscribe(channel)
        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            data = message['data']
            # message data is already a JSON string or raw bytes
            if isinstance(data, bytes):
                text = data.decode()
            else:
                text = str(data)
            yield f"data: {text}\n\n"
    return Response(generate(), mimetype='text/event-stream')

@bp.route('/<int:project_id>/cancel', methods=['DELETE'])
def cancel_project(project_id):
    task_id = request.args.get('task_id')
    from celery.result import AsyncResult
    result = AsyncResult(task_id, app=current_app.extensions['celery'])
    result.revoke(terminate=True)
    return {'status': 'cancelled'}, 200
