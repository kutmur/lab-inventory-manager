from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    registry_number = StringField('Registry Number', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    unit = StringField('Unit', validators=[DataRequired()])
    minimum_quantity = FloatField('Minimum Quantity', validators=[NumberRange(min=0)])
    location_in_lab = StringField('Location in Lab')
    notes = TextAreaField('Notes')
    lab_id = SelectField('Lab', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class TransferForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = FloatField('Quantity to Transfer', validators=[DataRequired(), NumberRange(min=0.01)])
    source_lab_id = SelectField('Source Lab', coerce=int, validators=[DataRequired()])
    destination_lab_id = SelectField('Destination Lab', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Transfer')

class LabForm(FlaskForm):
    name = StringField('Lab Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    location = StringField('Location')
    submit = SubmitField('Submit') 