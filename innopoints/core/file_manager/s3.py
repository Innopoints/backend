"""Manages static files. This particular module uses the AWS S3 to store files."""

import requests

from .base import FileManagerBase, FileStorage


class FileManagerS3(FileManagerBase):
    """Implementation of file manager using Amazon S3."""
    def __init__(self, url='http://innopoints.s3.amazonaws.com'):
        super().__init__(url)

    def retrieve(self, handle: str, namespace: str) -> bytes:
        """Get the file with a given URL from the AWS S3 bucket."""
        response = requests.get(f'{self.BASE_PATH}/{namespace}/{handle}')
        if response.status_code == 404:
            raise FileNotFoundError()

        return response.content

    def store(self, file: FileStorage, handle: str, namespace: str):
        """Upload the given file with the handle to the namespace directory
        of the AWS S3 bucket. Will raise a requests.exceptions.HTTPError on errors."""
        filename = f'{namespace}/{handle}'
        stream = file.stream
        response = requests.post(self.BASE_PATH, data={'key': filename}, files={'file': stream})
        response.raise_for_status()

    def delete(self, handle: str, namespace: str):
        """Delete the file with a given handle from the namespace of the AWS S3 bucket."""
        response = requests.delete(f'{self.BASE_PATH}/{namespace}/{handle}')
        if response.status_code == 404:
            raise FileNotFoundError()
