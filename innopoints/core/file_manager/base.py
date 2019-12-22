"""Provides a base interface for the file management modules to implement"""
from abc import ABC, abstractmethod
from werkzeug.datastructures import FileStorage


class FileManagerBase(ABC):
    """Base abstract class as an interface for file managers"""
    BASE_PATH = ''

    @abstractmethod
    def retrieve(self, handle: str, namespace: str) -> bytes:
        """Get the file with the given handle and namespace"""

    @abstractmethod
    def store(self, file: FileStorage, handle: str, namespace: str):
        """Store the given file with the given name under the given namespace"""

    @abstractmethod
    def delete(self, handle: str, namespace: str):
        """Delete the file with given handle and namespace"""
