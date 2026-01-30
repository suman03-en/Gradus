import os
import uuid
from datetime import datetime

def submission_upload_path(instance, filename):
    """
    Professional file path for student submissions.
    Format:
    uploads/<classroom_slug_or_id>/<task_slug_or_id>/<student_id>/<timestamp>_<uuid>_<original_filename>
    """
    # Safe task name
    task_slug = instance.task.name.replace(" ", "_")
    
    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Unique ID
    unique_id = uuid.uuid4().hex
    
    # File extension
    ext = os.path.splitext(filename)[1]
    
    # Original filename safe
    original_name = os.path.splitext(filename)[0].replace(" ", "_")
    
    # Final filename
    final_filename = f"{timestamp}_{unique_id}_{original_name}{ext}"
    
    # Full path
    return os.path.join(
        "uploads",
        str(instance.task.classroom.id),
        f"{instance.task.id}_{task_slug}",
        str(instance.student.id),
        final_filename
    )
