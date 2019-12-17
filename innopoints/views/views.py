"""Application views"""

from flask import abort, request
from flask.views import MethodView
from flask_login import login_required, current_user
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from innopoints.extensions import db
from innopoints.blueprints import api
from innopoints.models import (
    Competence,
)
from innopoints.schemas import (
    CompetenceSchema,
)

NO_PAYLOAD = ('', 204)


# ----- Competence -----

@api.route('/competences')
def list_competences():
    """List all of the existing competences."""

    schema = CompetenceSchema(many=True)
    return schema.jsonify(Competence.query.all())


@api.route('/competences', methods=['POST'])
@login_required
def create_competence():
    """Create a new competence."""
    if not request.is_json:
        abort(400, {'message': 'The request should be in JSON.'})

    if not current_user.is_admin:
        abort(401)

    in_schema = CompetenceSchema(exclude=('id',))

    try:
        new_competence = in_schema.load(request.json)
    except ValidationError as err:
        abort(400, {'message': err.messages})

    try:
        db.session.add(new_competence)
        db.session.commit()
    except IntegrityError as err:
        db.session.rollback()
        print(err)  # TODO: replace with proper logging
        abort(400, {'message': 'Data integrity violated.'})

    out_schema = CompetenceSchema()
    return out_schema.jsonify(new_competence)


class CompetenceAPI(MethodView):
    """REST views for a particular instance of a Competence model."""

    @login_required
    def patch(self, compt_id):
        """Edit the competence."""
        if not request.is_json:
            abort(400, {'message': 'The request should be in JSON.'})

        competence = Competence.query.get_or_404(compt_id)
        if not current_user.is_admin:
            abort(401)

        in_schema = CompetenceSchema(exclude=('id',))

        try:
            updated_competence = in_schema.load(request.json, instance=competence, partial=True)
        except ValidationError as err:
            abort(400, {'message': err.messages})

        try:
            db.session.add(updated_competence)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})

        out_schema = CompetenceSchema()
        return out_schema.jsonify(updated_competence)

    @login_required
    def delete(self, compt_id):
        """Delete the competence."""
        competence = Competence.query.get_or_404(compt_id)

        try:
            db.session.delete(competence)
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            print(err)  # TODO: replace with proper logging
            abort(400, {'message': 'Data integrity violated.'})
        return NO_PAYLOAD


competence_api = CompetenceAPI.as_view('competence_api')
api.add_url_rule('/competences/<int:compt_id>',
                 view_func=competence_api,
                 methods=('PATCH', 'DELETE'))
