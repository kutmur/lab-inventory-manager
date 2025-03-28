from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from app.models import Lab

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    registry_number = StringField('Registry Number', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0, message="Quantity must be greater than or equal to 0")])
    unit = SelectField('Unit', choices=[
        ('Adet', 'Adet'),
        ('Paket', 'Paket'),
        ('Kutu', 'Kutu')
    ], validators=[DataRequired()])
    minimum_quantity = FloatField('Minimum Quantity', validators=[DataRequired(), NumberRange(min=0, message="Minimum quantity must be greater than or equal to 0")])
    lab_id = SelectField('Lab', coerce=int, validators=[DataRequired()])
    cabinet_number = SelectField('Cabinet Number', coerce=str, validators=[DataRequired()])
    notes = StringField('Notes')
    submit = SubmitField('Add Product')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Get all predefined labs and sort them by code
        labs = Lab.get_predefined_labs()
        self.lab_id.choices = [(lab.id, f"{lab.code} - {lab.description}") for lab in labs]
        # Initialize cabinet choices as empty (will be populated via JavaScript)
        self.cabinet_number.choices = []
        self.cabinet_number.render_kw = {'disabled': True}

    def validate_quantity(self, field):
        try:
            float(field.data)
        except (ValueError, TypeError):
            raise ValidationError('Quantity must be a valid number')

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