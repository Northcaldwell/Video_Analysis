from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename
from src import db
from src.models import Project, File
from sqlalchemy.exc import IntegrityError
import os

bp = Blueprint(
    'main',
    __name__,
    template_folder='../templates'
)

@bp.route('/', methods=['GET'])
def index():
    """Redirect root to the upload form."""
    return redirect(url_for('main.upload_form'))

@bp.route('/upload', methods=['GET'])
def upload_form():
    """Show the upload form."""
    return render_template('upload.html')

@bp.route('/upload', methods=['POST'])
def upload():
    """Handle file uploads and create a Project."""
    case_number = request.form['case_number']
    email       = request.form.get('email')
    files       = request.files.getlist('files')

    # Prevent duplicate case numbers
    existing = Project.query.filter_by(case_number=case_number).first()
    if existing:
        flash(f"Case {case_number} already exists. Redirecting to its processing page.")
        return redirect(url_for('processing.dashboard', project_id=existing.id))

    # Create new project
    project = Project(case_number=case_number, email=email, status='pending')
    db.session.add(project)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Error creating project. Try a different case number.")
        return redirect(url_for('main.index'))

    # Save files to uploads/<project_id>/
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    upload_dir   = os.path.join(project_root, 'uploads', str(project.id))
    os.makedirs(upload_dir, exist_ok=True)

    for f in files:
        filename = secure_filename(f.filename)
        dest = os.path.join(upload_dir, filename)
        f.save(dest)
        db.session.add(File(project_id=project.id, filename=filename, status='pending'))
    db.session.commit()

    return redirect(url_for('processing.dashboard', project_id=project.id))