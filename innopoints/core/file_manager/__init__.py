"""File manager module."""
from .s3 import FileManagerS3
from .local import FileManagerLocal

file_manager = FileManagerLocal()
