"""Local file storage for uploaded images (used by fastapi-storages)."""

import os

from fastapi_storages import FileSystemStorage

# Base directory for uploads. In Docker this is a mounted volume.
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def setup_storage() -> None:
    """Ensure the upload directory exists (idempotent)."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


setup_storage()

# Files are stored directly under UPLOAD_DIR and served at /uploads/<name>.
storage = FileSystemStorage(path=UPLOAD_DIR)
