"""Manages static files. This particular module uses the AWS S3 to store files"""

import os
from werkzeug.datastructures import FileStorage

STORAGE_BASE = './static_files'

if not os.path.exists(STORAGE_BASE):
    os.makedirs(STORAGE_BASE)

def _join_base(*paths: str) -> str:
    """Helper function to join path to base and normalize it according to OS."""
    return os.path.normpath(os.path.join(STORAGE_BASE, *paths))


def retrieve(handle: str, namespace: str) -> bytes:
    """Get the file with a given URL from the AWS S3 bucket."""
    path = _join_base(namespace, handle)
    if not os.path.exists(path):
        raise FileNotFoundError()
    file = open(path, 'rb')
    return file.read()


def store(file: FileStorage, handle: str, namespace: str):
    """Upload the given file with the handle to the namespace directory
       of the AWS S3 bucket. Will raise a requests.exceptions.HTTPError on errors"""
    folder = _join_base(namespace)
    if not os.path.exists(folder):
        os.makedirs(folder)
    filename = os.path.join(folder, handle)
    file.save(filename)


def delete(handle: str, namespace: str):
    """Delete the file with a given handle from the namespace of the AWS S3 bucket."""
    folder = _join_base(namespace)
    if not os.path.exists(folder):
        raise FileNotFoundError()
    filename = os.path.join(folder, handle)
    os.remove(filename)
    # directory is now empty ?
    if not os.listdir(folder):
        os.rmdir(folder)
