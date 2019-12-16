"""Model schemas for serialization."""

from marshmallow import validate, validates_schema, ValidationError, pre_load, post_dump
from innopoints.extensions import ma, db
from marshmallow_enum import EnumField

from innopoints.models import (
    Account,
    Activity,
    Application,
    ApplicationStatus,
    Color,
    Competence,
    Product,
    ProductImage,
    Size,
    StockChange,
    StockChangeStatus,
    Variety,
    db
)


# pylint: disable=missing-docstring
# pylint: disable=no-member



class ActivitySchema(ma.ModelSchema):
    class Meta:
        model = Activity
        ordered = True
        exclude = ('project_id', 'notifications')
        sqla_session = db.session

    @pre_load
    def unwrap_dates(self, data, **kwargs):  # pylint: disable=unused-argument
        """Expand the {"start": , "end": } dates object into two separate properties."""
        try:
            dates = data.pop('timeframe')
            data['start_date'] = dates['start']
            data['end_date'] = dates['end']
        except KeyError:
            raise ValidationError("The date range has a wrong format.")

        return data

    @post_dump
    def wrap_dates(self, data, **kwargs):  # pylint: disable=unused-argument
        """Collapse the two date properties into the {"start": , "end": } dates object."""
        data['timeframe'] = {
            'start': data.pop('start_date'),
            'end': data.pop('end_date')
        }
        return data

    @validates_schema
    def work_hours_mutex(self, data, **kwargs):  # pylint: disable=unused-argument
        """Ensure that working hours aren't specified along with the reward_rate."""
        if 'work_hours' in data and 'reward_rate' in data:
            raise ValidationError('Working hours and reward rate are mutually exclusive.')

    @validates_schema
    def valid_date_range(self, data, **kwargs):  # pylint: disable=unused-argument
        """Ensure that the start date is not beyond the end date."""
        start = data['start_date']
        end = data['end_date']

        if start > end:
            raise ValidationError('The start date is beyond the end date.')

    def get_applications(self, activity):
        fields = ['id', 'applicant']
        filtering = {'activity_id': activity.id,
                     'status': ApplicationStatus.approved}

        if not self.context['user'].is_authenticated:
            return None

        if self.context['user'] in activity.project.moderators:
            filtering.pop('status')
            fields.append('telegram_username')
            fields.append('comment')

        appl_schema = ApplicationSchema(only=fields, many=True)
        applications = Application.query.filter_by(**filtering)
        return appl_schema.dump(applications.all())

    def get_existing_application(self, activity):
        """Using the user information from the context, provide a shorthand
        for the existing application of a volunteer."""
        appl_schema = ApplicationSchema(only=('id', 'telegram_username', 'comment'))
        if self.context['user'].is_authenticated:
            application = Application.query.filter_by(applicant_email=self.context['user'].email,
                                                      activity_id=activity.id).one_or_none()
            if application is None:
                return None
            return appl_schema.dump(application)
        return None

    working_hours = ma.Int(validate=validate.Range(min=1))
    reward_rate = ma.Int(validate=validate.Range(min=1))
    people_required = ma.Int(validate=validate.Range(min=0))
    application_deadline = ma.DateTime(format='iso', data_key='application_deadline')
    vacant_spots = ma.Int(dump_only=True)
    applications = ma.Method(serialize='get_applications',
                             dump_only=True)
    existing_application = ma.Method(serialize='get_existing_application',
                                     dump_only=True)


class ApplicationSchema(ma.ModelSchema):
    class Meta:
        model = Application
        ordered = True
        sqla_session = db.session
        exclude = ('report', 'feedback')

    status = EnumField(ApplicationStatus)
    applicant = ma.Nested('AccountSchema', only=('full_name', 'email'))
    telegram_username = ma.Str(data_key='telegram')



class ProductSchema(ma.ModelSchema):
    class Meta:
        model = Product
        ordered = True
        sqla_session = db.session

    varieties = ma.Nested('VarietySchema', many=True)
    name = ma.Str(validate=validate.Length(min=1, max=128))
    type = ma.Str(validate=validate.Length(min=1, max=128), allow_none=True)
    description = ma.Str(validate=validate.Length(max=1024))
    price = ma.Int(validate=validate.Range(min=1))


class VarietySchema(ma.ModelSchema):
    class Meta:
        model = Variety
        ordered = True
        include_fk = True
        sqla_session = db.session

    @pre_load
    def create_stock_change(self, data, **kwargs):  # pylint: disable=unused-argument
        if 'stock_changes' in data:
            raise ValidationError('The stock changes are not to be specified explicitly.')

        if self.context.get('update', False):
            return data

        if 'amount' not in data:
            raise ValidationError('The amount for a variety is not specified.')

        amount = data.pop('amount')
        data['stock_changes'] = [{
            'amount': amount,
            'account_email': self.context['user'].email,
            'status': 'carried_out',
        }]
        return data

    @pre_load
    def wire_color_size(self, data, **kwargs):  # pylint: disable=unused-argument
        if self.context.get('update', False):
            if 'size' in data:
                data['size_id'] = data.pop('size')
            if 'color' in data:
                data['color_value'] = data.pop('color')
        else:
            try:
                data['size_id'] = data.pop('size')
                data['color_value'] = data.pop('color')
            except KeyError:
                raise ValidationError('Size and color must be specified.')

        if 'color_value' not in data or data['color_value'] is None:
            return data

        if data['color_value'].startswith('#'):
            data['color_value'] = data['color_value'][1:].upper()

        if len(data['color_value']) != 6:
            raise ValidationError(
                f'The color value is {len(data["color_value"])} characters long, 6 expected.')

        return data

    @pre_load
    def enumerate_images(self, data, **kwargs):  # pylint: disable=unused-argument
        if self.context.get('update', False):
            if 'images' in data:
                data['images'] = [{'order': idx, 'image_id': int(url.split('/')[2])}
                                  for (idx, url) in enumerate(data['images'], start=1)]
        else:
            try:
                data['images'] = [{'order': idx, 'image_id': int(url.split('/')[2])}
                                  for (idx, url) in enumerate(data['images'], start=1)]
            except KeyError:
                raise ValidationError('Images must be specified.')
        return data

    @post_dump
    def unwire_color_size(self, data, **kwargs):  # pylint: disable=unused-argument
        data['size'] = data.pop('size_id')
        if data['color_value'] is None:
            data['color'] = data.pop('color_value')
        else:
            data['color'] = '#' + data.pop('color_value')
        return data

    @post_dump
    def flatten_images(self, data, **kwargs):  # pylint: disable=unused-argument
        data['images'] = [f'/file/{image["image_id"]}'
                          for image in sorted(data['images'],
                                              key=lambda x: x['order'])]
        return data

    images = ma.Nested('ProductImageSchema', many=True)
    stock_changes = ma.Nested('StockChangeSchema', many=True)
    amount = ma.Int(dump_only=True)
    purchases = ma.Int(dump_only=True)


class CompetenceSchema(ma.ModelSchema):
    class Meta:
        model = Competence
        ordered = True
        sqla_session = db.session
        exclude = ('activities', 'feedback')


class ColorSchema(ma.ModelSchema):
    class Meta:
        model = Color
        ordered = True
        sqla_session = db.session
        exclude = ('varieties',)

    @pre_load
    def normalize_value(self, data, **kwargs):  # pylint: disable=unused-argument
        """Normalize the color value, stripping the '#' and transforming symbols to uppercase."""
        if data['value'].startswith('#'):
            data['value'] = data['value'][1:]

        if len(data['value']) != 6:
            raise ValidationError(
                f'The color value is {len(data["value"])} characters long, 6 expected.')

        data['value'] = data['value'].upper()

        if not all(char in '0123456789ABCDEF' for char in data['value']):
            raise ValidationError('The color value contains non-hex symbols.')

        return data

    @post_dump
    def precede_hash(self, data, **kwargs):  # pylint: disable=unused-argument
        """Precede the value of the color with a '#' symbol."""
        data['value'] = '#' + data['value']
        return data


class SizeSchema(ma.ModelSchema):
    class Meta:
        model = Size
        ordered = True
        sqla_session = db.session
        exclude = ('varieties',)


class StockChangeSchema(ma.ModelSchema):
    class Meta:
        model = StockChange
        ordered = True
        include_fk = True
        sqla_session = db.session

    status = EnumField(StockChangeStatus)


class ProductImageSchema(ma.ModelSchema):
    class Meta:
        model = ProductImage
        ordered = True
        include_fk = True
        sqla_session = db.session
