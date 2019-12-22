"""Manages static files. This particular module uses local file system to store files"""

import os
from werkzeug.datastructures import FileStorage

from .base import FileManagerBase


class FileManagerLocal(FileManagerBase):
    """Implementation of the file manager using local file system"""
    def __init__(self, url='./static_files'):
        super().__init__(url)
        if not os.path.exists(url):
            os.makedirs(url)


    def _join_base(self, *paths: str) -> str:
        """Helper function to join path to base and normalize it according to OS."""
        return os.path.normpath(os.path.join(self.BASE_PATH, *paths))


    def retrieve(self, handle: str, namespace: str) -> bytes:
        """Get the file with given handle from the given namespace (folder)."""
        path = self._join_base(namespace, handle)
        if not os.path.exists(path):
            raise FileNotFoundError()
        file = open(path, 'rb')
        return file.read()


    def store(self, file: FileStorage, handle: str, namespace: str):
        """Upload the given file with the handle to the namespace directory."""
        folder = self._join_base(namespace)
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = os.path.join(folder, handle)
        file.save(filename)


    def delete(self, handle: str, namespace: str):
        """Delete the file with a given handle from the namespace"""
        folder = self._join_base(namespace)
        if not os.path.exists(folder):
            raise FileNotFoundError()
        filename = os.path.join(folder, handle)
        os.remove(filename)
        # directory is now empty ?
        if not os.listdir(folder):
            os.rmdir(folder)
