# app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import (StringField, FloatField, TextAreaField, SelectField,
                     SubmitField)
from wtforms.validators import DataRequired, NumberRange, ValidationError
from app.models import Lab


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    registry_number = StringField('Registry Number', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message="Quantity must be >= 0")
    ])
    unit = SelectField('Unit', choices=[
        ('Adet', 'Adet'),
        ('Paket', 'Paket'),
        ('Kutu', 'Kutu')
    ], validators=[DataRequired()])
    minimum_quantity = FloatField('Minimum Quantity', validators=[
        DataRequired(),
        NumberRange(min=0, message="Minimum quantity must be >= 0")
    ])

    lab_id = SelectField('Lab', coerce=int, validators=[DataRequired()])
    location_number = SelectField('Location', coerce=str, validators=[DataRequired()])

    notes = StringField('Notes')
    submit = SubmitField('Save Product')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tüm lab'ları çekip select'e ekliyoruz (predefined veya Lab.query.all)
        labs = Lab.get_predefined_labs()
        self.lab_id.choices = [
            (lab.id, f"{lab.code} - {lab.description}") for lab in labs
        ]
        # Location alanını JS ile dolduracağımız için başlangıçta boş tutuyoruz
        self.location_number.choices = []
        # disabled => Javascript ile "lab" seçilince aktif edilecek
        self.location_number.render_kw = {'disabled': True}

    def get_location_choices(self, lab_id):
        """Seçili lab'a göre konum (workspace / dolap) listesi döndürür."""
        lab = Lab.query.get(lab_id)
        if not lab:
            return []
        
        choices = [
            ('workspace', 'Çalışma Alanı')
        ]
        for cabinet_num in range(1, lab.max_cabinets + 1):
            choices.append(
                (f"cabinet-{cabinet_num}-upper", f"Dolap No: {cabinet_num} - Üst")
            )
            choices.append(
                (f"cabinet-{cabinet_num}-lower", f"Dolap No: {cabinet_num} - Alt")
            )
        return choices

    def validate_quantity(self, field):
        # Sayısal olmalı
        try:
            float(field.data)
        except (ValueError, TypeError):
            raise ValidationError('Quantity must be a valid float number')


class TransferForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = FloatField('Quantity to Transfer', validators=[
        DataRequired(),
        NumberRange(min=0.01, message="Transfer quantity must be > 0")
    ])
    source_lab_id = SelectField('Source Lab', coerce=int, validators=[DataRequired()])
    destination_lab_id = SelectField('Destination Lab', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Transfer')


class LabForm(FlaskForm):
    name = StringField('Lab Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    location = StringField('Location')
    submit = SubmitField('Submit')
