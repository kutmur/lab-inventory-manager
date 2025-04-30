from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    IntegerField,
    TextAreaField,
    SelectField,
    SubmitField
)
from wtforms.validators import DataRequired, NumberRange, ValidationError
from app.models import Lab

class ProductForm(FlaskForm):
    """
    Form for adding or editing a product.
    'location' field is dynamically populated based on selected lab.
    """
    name = StringField('Product Name', validators=[DataRequired()])
    registry_number = StringField('Registry Number', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message="Quantity must be 0 or greater")
    ])
    unit = SelectField('Unit', choices=[
        ('Adet', 'Adet'),
        ('Paket', 'Paket'),
        ('Kutu', 'Kutu')
    ], validators=[DataRequired()])
    minimum_quantity = IntegerField('Minimum Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message="Minimum quantity must be 0 or greater")
    ])

    lab_id = SelectField('Lab', coerce=int, validators=[DataRequired()])
    location = SelectField('Location', validators=[DataRequired()])
    
    notes = TextAreaField('Notes')
    submit = SubmitField('Save Product')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Always populate labs list from predefined labs
        labs = Lab.get_predefined_labs()
        self.lab_id.choices = [
            (lab.id, f"{lab.code} - {lab.name}") for lab in labs
        ]

        # If form is being submitted or loaded with obj, provide selections
        if self.lab_id.data:
            self.location.choices = self.get_location_choices(self.lab_id.data)
            self.location.render_kw = {}
        else:
            # Otherwise keep it disabled initially
            self.location.choices = []
            self.location.render_kw = {'disabled': True}

    def get_location_choices(self, lab_id):
        """
        Returns location choices (workspace / cabinet) based on selected lab.
        """
        lab = Lab.query.get(lab_id)
        if not lab:
            return []

        choices = [('workspace', 'Workspace')]
        for cabinet_num in range(1, lab.max_cabinets + 1):
            choices.append(
                (f"cabinet-{cabinet_num}-upper", f"Cabinet #{cabinet_num} - Upper")
            )
            choices.append(
                (f"cabinet-{cabinet_num}-lower", f"Cabinet #{cabinet_num} - Lower")
            )
        return choices

    def validate_quantity(self, field):
        """Validate quantity is a whole number"""
        try:
            value = int(field.data)
            if value != field.data:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValidationError('Quantity must be a whole number')

    def validate_minimum_quantity(self, field):
        """Validate minimum quantity is a whole number"""
        try:
            value = int(field.data)
            if value != field.data:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValidationError('Minimum quantity must be a whole number')


class TransferForm(FlaskForm):
    """
    Form for transferring a product between labs.
    """
    source_lab_id = SelectField('Source Laboratory', coerce=int, validators=[DataRequired()], render_kw={'disabled': 'disabled'})
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    destination_lab_id = SelectField('Destination Laboratory', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity to Transfer', validators=[
        DataRequired(),
        NumberRange(min=1, message="Transfer quantity must be at least 1")
    ])
    notes = TextAreaField('Notes')
    submit = SubmitField('Confirm Transfer')

    def __init__(self, *args, source_lab_id=None, max_quantity=None, **kwargs):
        super().__init__(*args, **kwargs)
        if source_lab_id:
            self.source_lab_id.data = source_lab_id
            # Exclude source lab from destination choices
            self.destination_lab_id.choices = [
                (lab.id, f"{lab.code} - {lab.name}")
                for lab in Lab.query.filter(Lab.id != source_lab_id).all()
            ]
        if max_quantity:
            self.quantity.validators.append(
                NumberRange(max=max_quantity, message=f"Cannot transfer more than available quantity ({max_quantity})")
            )


class LabForm(FlaskForm):
    """
    Form for adding or editing a laboratory - disabled as per requirements.
    """
    name = StringField('Lab Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    location = StringField('Location')
    submit = SubmitField('Submit')
