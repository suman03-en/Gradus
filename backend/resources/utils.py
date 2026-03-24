import os
import uuid
import zipfile
from django.conf import settings


def get_max_upload_size_bytes():
    return int(getattr(settings, "RESOURCE_MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024))


def get_allowed_mime_types():
    return {
        "pdf": ["application/pdf"],
        "doc": ["application/msword", "application/vnd.ms-office"],
        "docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ],
        "jpg": ["image/jpeg"],
        "jpeg": ["image/jpeg"],
        "png": ["image/png"],
        "txt": ["text/plain"],
        "zip": ["application/zip"],
        "pptx": [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        ],
    }


def _reset_file_position(uploaded_file, original_position):
    try:
        uploaded_file.seek(original_position)
    except Exception:
        # Some file wrappers may not support seeking; ignore gracefully.
        pass


def _peek_bytes(uploaded_file, size):
    original_position = 0
    try:
        original_position = uploaded_file.tell()
    except Exception:
        pass

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    data = uploaded_file.read(size)
    _reset_file_position(uploaded_file, original_position)
    return data


def _detect_openxml_mime(uploaded_file):
    original_position = 0
    try:
        original_position = uploaded_file.tell()
        uploaded_file.seek(0)
        with zipfile.ZipFile(uploaded_file) as archive:
            names = archive.namelist()
            if any(name.startswith("word/") for name in names):
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if any(name.startswith("ppt/") for name in names):
                return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        return "application/zip"
    except Exception:
        return "application/zip"
    finally:
        _reset_file_position(uploaded_file, original_position)


def detect_mime_type(uploaded_file):
    header = _peek_bytes(uploaded_file, 8192)

    if header.startswith(b"%PDF-"):
        return "application/pdf"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "application/msword"
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return _detect_openxml_mime(uploaded_file)

    # Treat UTF-8 decodable files as text/plain.
    try:
        header.decode("utf-8")
        return "text/plain"
    except Exception:
        return "application/octet-stream"


def scan_for_malware(uploaded_file):
    # Minimal always-on pipeline: detect EICAR signature and allow optional future engine integration.
    # The upload can be blocked if this scan fails depending on settings.
    original_position = 0
    try:
        original_position = uploaded_file.tell()
    except Exception:
        pass

    try:
        uploaded_file.seek(0)
    except Exception:
        pass

    data = uploaded_file.read()
    _reset_file_position(uploaded_file, original_position)

    eicar_signature = (
        b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    )
    if eicar_signature in data:
        return False, "Malware signature detected (EICAR)."

    return True, "Scan passed."


def resource_upload_path(instance, filename):
    """
    Format:
    resources/<content_type>/<object_id>/<new_filename>
    """
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    content_type_str = str(instance.content_type.model)
    return os.path.join(
        "resources", content_type_str, str(instance.object_id), new_filename
    )
