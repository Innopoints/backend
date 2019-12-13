"""Manages static files. This particular module uses the AWS S3 to store files"""

import io

import requests


S3_BUCKET_URL = 'http://innopoints.s3.amazonaws.com'


def retrieve(url: str) -> bytes:
    """Get the file with a given URL from the AWS S3 bucket."""
    response = requests.get(f'{S3_BUCKET_URL}/{url}')
    if response.status_code == 404:
        return None
    
    return response.content


def store(file: io.BytesIO, handle: str, namespace: str):
    """Upload the given file with the handle to the namespace directory
       of the AWS S3 bucket. Will raise a requests.exceptions.HTTPError on errors"""
    filename = f'{namespace}/{handle}'
    response = requests.post(S3_BUCKET_URL, data={'key': filename}, files={'file': file})
    response.raise_for_status()


def delete(handle: str, namespace: str):
    """Delete the file with a given handle from the namespace of the AWS S3 bucket."""
    requests.delete(f'{S3_BUCKET_URL}/{namespace}/{handle}')
