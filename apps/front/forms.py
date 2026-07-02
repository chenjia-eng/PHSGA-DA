from wtforms import StringField, IntegerField
from wtforms.validators import InputRequired, Length, Email, EqualTo, Regexp
from ..forms import BaseForm

from .models import SampleModel
from wtforms import ValidationError
from flask import g


class SampleForm(BaseForm):
    content = StringField(validators=[InputRequired(message='Please enter serial information.')])
    check = IntegerField()


class RetrieveForm(BaseForm):
    uuid = StringField(validators=[InputRequired(message='Please enter the task id.')])

    def validate_uuid(self, field):
        uuid = field.data
        if not SampleModel.query.filter_by(sample_name=uuid).first():
            raise ValidationError('The task does not exist or has expired.')