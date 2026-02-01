import os
import uuid
from django.utils.text import slugify

def submission_upload_path(instance, filename):
    """
    Professional file path for student submissions.
    Format:
    uploads/<task_id>/<task_slug>/<new_filename>
    """
    ext = filename.split('.')[-1]  # Keep original extension
    task_slug = slugify(instance.task.name)[:50]  # max 50 chars
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("uploads", str(instance.task.id), task_slug, new_filename)

