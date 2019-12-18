import mimetypes
import requests
import werkzeug
from flask import abort, jsonify, request, current_app
from flask_login import login_required

from innopoints.extensions import db
from innopoints.blueprints import api
import innopoints.file_manager_s3 as file_manager
from innopoints.models import StaticFile


ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}


def get_mimetype(file: werkzeug.FileStorage) -> str:  # pylint: disable=no-member
    """Return a MIME type of a Flask file object"""
    if file.mimetype:
        return file.mimetype

    return mimetypes.guess_type(file.filename)[0]


@api.route('/file/<namespace>', methods=['POST'])
@login_required
def upload_file(namespace):
    """Upload a file to a given namespace."""
    if 'file' not in request.files:
        abort(400, {'message': 'No file attached.'})

    file = request.files['file']

    if not file.filename:
        abort(400, {'message': 'The file doesn\'t have a name.'})

    mimetype = get_mimetype(file)
    if mimetype not in ALLOWED_MIMETYPES:
        abort(400, {'message': f'Mimetype "{mimetype}" is not allowed'})

    new_file = StaticFile(mimetype=mimetype, namespace=namespace)
    db.session.add(new_file)
    db.session.commit()
    try:
        file_manager.store(file.stream, str(new_file.id), new_file.namespace)
    except requests.exceptions.HTTPError as exc:
        print(exc)  # TODO: replace with proper logging
        db.session.delete(new_file)
        db.session.commit()
        abort(400, {'message': 'Upload failed.'})
    return jsonify(id=new_file.id, url=f'/file/{new_file.id}')


@api.route('/file/<int:file_id>')
def retrieve_file(file_id):
    """Get the chosen static file"""
    file = StaticFile.query.get_or_404(file_id)
    url = f'{file.namespace}/{file.id}'
    file_data = file_manager.retrieve(url)

    if file_data is None:
        abort(404)

    response = current_app.make_response(file_data)
    response.headers.set('Content-Type', file.mimetype)
    return response
