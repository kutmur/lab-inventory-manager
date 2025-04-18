from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FloatField,
    TextAreaField,
    SelectField,
    SubmitField
)
from wtforms.validators import DataRequired, NumberRange, ValidationError
from app.models import Lab

class ProductForm(FlaskForm):
    """
    Yeni bir ürün (Product) eklemek veya düzenlemek için kullanılan form.
    'location_number' alanı, hem sunucu hem de JS tarafında dinamik şekilde doldurulacak.
    """
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

        # Lab listesini her zaman doldur
        labs = Lab.get_predefined_labs()
        self.lab_id.choices = [
            (lab.id, f"{lab.code} - {lab.description}") for lab in labs
        ]

        # Eğer form POST edilmiş veya obj ile gelmişse, seçimleri sun
        if self.lab_id.data:
            self.location_number.choices = self.get_location_choices(self.lab_id.data)
            self.location_number.render_kw = {}
        else:
            # Aksi halde başlangıçta pasif kalsın
            self.location_number.choices = []
            self.location_number.render_kw = {'disabled': True}

    def get_location_choices(self, lab_id):
        """
        Seçili lab'a göre location (workspace / dolap) listesi döndürür.
        """
        lab = Lab.query.get(lab_id)
        if not lab:
            return []

        choices = [('workspace', 'Çalışma Alanı')]
        for cabinet_num in range(1, lab.max_cabinets + 1):
            choices.append(
                (f"cabinet-{cabinet_num}-upper", f"Dolap No: {cabinet_num} - Üst")
            )
            choices.append(
                (f"cabinet-{cabinet_num}-lower", f"Dolap No: {cabinet_num} - Alt")
            )
        return choices

    def validate_quantity(self, field):
        """
        Ek validasyon: sayının parse edilebildiğinden emin ol.
        """
        try:
            float(field.data)
        except (ValueError, TypeError):
            raise ValidationError('Quantity must be a valid float number')


class TransferForm(FlaskForm):
    """
    Bir ürünü bir laboratuvardan diğerine aktarmak için gereken form.
    """
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
    """
    Yeni bir laboratuvar eklemek veya düzenlemek için form.
    """
    name = StringField('Lab Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    location = StringField('Location')
    submit = SubmitField('Submit')
