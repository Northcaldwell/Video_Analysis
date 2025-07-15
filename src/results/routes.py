from flask import Blueprint, render_template, current_app, send_file, abort
from src.models import Project, File, Detection
from io import BytesIO
import zipfile
import os

bp = Blueprint(
    'results',
    __name__,
    template_folder='templates',
    url_prefix='/results'
)

@bp.route('/<int:project_id>', methods=['GET'])
def overview(project_id):
    project = Project.query.get_or_404(project_id)
    files = File.query.filter_by(project_id=project_id).all()
    file_data = []
    for f in files:
        dets = Detection.query.filter_by(file_id=f.id).all()
        file_data.append({
            'file': f,
            'detections': dets
        })
    return render_template('results.html', project=project, file_data=file_data)

@bp.route('/<int:project_id>/export_pdf', methods=['GET'])
def export_pdf(project_id):
    try:
        from weasyprint import HTML
    except ImportError:
        abort(500, description="WeasyPrint not installed")

    html = render_template('report_template.html', project=Project.query.get_or_404(project_id), file_data=[{'file':f, 'detections':Detection.query.filter_by(file_id=f.id).all()} for f in File.query.filter_by(project_id=project_id)])
    pdf = HTML(string=html, base_url=current_app.root_path).write_pdf()
    return send_file(BytesIO(pdf), download_name=f"report_{project_id}.pdf", mimetype='application/pdf')

@bp.route('/<int:project_id>/download_zip', methods=['GET'])
def download_zip(project_id):
    project_root = os.path.abspath(os.path.join(current_app.root_path, os.pardir))
    upload_dir = os.path.join(project_root, 'uploads', str(project_id))
    if not os.path.isdir(upload_dir):
        abort(404, description="Upload directory not found")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, project_root)
                zf.write(full_path, arcname)
    zip_buffer.seek(0)
    return send_file(zip_buffer, download_name=f"project_{project_id}.zip", as_attachment=True)