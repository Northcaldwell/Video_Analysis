from . import celery, db, mail
from src.models import Project, File, Detection
from flask_mail import Message
from flask import current_app
import redis
import time

@celery.task(bind=True)
def process_project(self, project_id, selected_plugins):
    project = Project.query.get(project_id)
    # get Redis client from Flask config
    redis_url = current_app.config.get("REDIS_URL", current_app.config["CELERY_BROKER_URL"])
    redis_client = redis.from_url(redis_url)

    # loop through files and plugins
    for f in project.files:
        redis_client.publish(f'project_{project_id}', f'Starting {f.filename}')
        for plugin in selected_plugins:
            # run your actual analysis here…
            time.sleep(1)  # placeholder for work
            redis_client.publish(f'project_{project_id}',
                                 f'Finished {plugin} on {f.filename}')
            # persist a Detection record (example)
            detection = Detection(
                file_id=f.id,
                frame=0,
                label=plugin,
                probability=0.99,
                details='Example run'
            )
            db.session.add(detection)
        db.session.commit()
        redis_client.publish(f'project_{project_id}', f'Completed file {f.filename}')

    # all done
    project.status = 'complete'
    db.session.commit()
    redis_client.publish(f'project_{project_id}', 'complete')

    # send notification email
    if project.email:
        msg = Message(
            subject=f"Project {project.case_number} Complete",
            recipients=[project.email],
            body=f"Your analysis is done: http://<your-host>/results/{project_id}"
        )
        mail.send(msg)
