import os
import uuid

def resource_upload_path(instance, filename):
    """
    Format:
    resources/<content_type>/<object_id>/<new_filename>
    """
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    content_type_str = str(instance.content_type.model)
    return os.path.join("resources", content_type_str, str(instance.object_id), new_filename)
