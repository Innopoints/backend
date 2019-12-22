"""File manager module."""
import os
from .s3 import FileManagerS3
from .local import FileManagerLocal

if int(os.getenv('USE_S3', '0')) == 1:
    file_manager = FileManagerS3()
else:
    file_manager = FileManagerLocal()
