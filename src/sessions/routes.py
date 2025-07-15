from flask import Blueprint, render_template, current_app, redirect, url_for, request, flash, jsonify, abort
from src.models import Project
from src import db
import os

bp = Blueprint(
    'sessions',
    __name__,
    template_folder='templates',
    url_prefix='/sessions'
)

@bp.route('/', methods=['GET'])
def list_sessions():
    # List all projects ordered by creation date
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('sessions.html', projects=projects)

@bp.route('/<int:project_id>/delete', methods=['POST'])
def delete_session(project_id):
    project = Project.query.get_or_404(project_id)
    # delete associated uploads/results directories
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    project_dir = os.path.join(project_root, 'uploads', str(project_id))
    try:
        if os.path.isdir(project_dir):
            import shutil
            shutil.rmtree(project_dir)
        db.session.delete(project)
        db.session.commit()
        flash(f"Session {project.case_number} deleted.", "success")
    except Exception as e:
        current_app.logger.error(f"Error deleting session {project_id}: {e}")
        flash("Error deleting session.", "danger")
    return redirect(url_for('sessions.list_sessions'))

@bp.route('/<int:project_id>/csv', methods=['GET'])
def export_csv(project_id):
    project = Project.query.get_or_404(project_id)
    # build CSV of detections
    from io import StringIO
    import csv
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['File', 'Frame', 'Label', 'Probability', 'Details'])
    for file in project.files:
        for det in file.detections:
            writer.writerow([file.filename, det.frame, det.label, det.probability, det.details])
    output = si.getvalue().encode('utf-8')
    from flask import send_file
    return send_file(
        BytesIO(output),
        download_name=f"detections_{project.case_number}.csv",
        mimetype='text/csv'
    )