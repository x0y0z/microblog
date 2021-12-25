import json
import sys
import time
from flask import render_template
from app import celery, create_app, db
from app.models import User, Post, Task
from app.email import send_email

app = create_app()
app.app_context().push()


def _set_task_progress(self, progress):
    self.update_state(state='STARTED' if progress == 0 else ('SUCCESS' if progress == 100 else 'PROGRESS'),
                      meta={'progress': progress})
    task = Task.query.get(self.request.id)
    if task:
        task.user.add_notification('task_progress', {'task_id': task.id,
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


@celery.task(bind=True)
def export_posts(self, user_id):
    try:
        user = User.query.get(user_id)
        _set_task_progress(self, 0)
        data = []
        i = 0
        total_posts = user.posts.count()
        for post in user.posts.order_by(Post.timestamp.asc()):
            data.append({'body': post.body,
                         'timestamp': post.timestamp.isoformat() + 'Z'})
            i += 1
            _set_task_progress(self, 100 * i // total_posts)

        send_email('[Microblog] Your blog posts',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_posts.txt', user=user),
                html_body=render_template('email/export_posts.html',
                                          user=user),
                attachments=[('posts.json', 'application/json',
                              json.dumps({'posts': data}, indent=4))],
                sync=True)
    except:
        _set_task_progress(self, 100)
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
