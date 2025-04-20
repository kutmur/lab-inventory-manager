# app/main/routes.py

import io
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, send_file, current_app, stream_with_context, Response
from flask_login import login_required, current_user
from docx import Document
from docx.shared import Inches
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from sqlalchemy.exc import IntegrityError
import pytz
from sqlalchemy.orm import joinedload

from app.main import bp
from app.main.forms import ProductForm, TransferForm, LabForm
from app.auth.decorators import admin_required
from app.models import Product, Lab, TransferLog, UserLog
from app.extensions import db, limiter
from app.utils import create_user_log
from app.socket_events import notify_inventory_update, notify_stock_alert
from app.models.product import ConcurrencyError


def format_timestamp(timestamp):
    """Convert UTC timestamp to Europe/Istanbul timezone"""
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    return timestamp.replace(tzinfo=pytz.UTC).astimezone(istanbul_tz)

def generate_excel(data):
    """Generate Excel file as a stream"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Lab Inventory', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Lab Inventory']
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            max_len = max(df[value].astype(str).apply(len).max(), len(value))
            worksheet.set_column(col_num, col_num, max_len + 2)
    
    output.seek(0)
    return output

def generate_pdf(data, lab_code=None):
    """Generate PDF file as a stream"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    elements = []
    styles = getSampleStyleSheet()
    title_text = f"Lab Inventory Report - {lab_code}" if lab_code else "Full Inventory Report"
    
    timestamp = format_timestamp(datetime.utcnow())
    elements.append(Paragraph(title_text, styles['Title']))
    elements.append(Paragraph(
        f"Generated on: {timestamp.strftime('%Y-%m-%d %H:%M')}",
        styles['Normal']
    ))
    
    # Create table data
    headers = ['Name', 'Registry #', 'Quantity', 'Unit', 'Min Qty', 'Location', 'Notes']
    if not lab_code:
        headers.insert(0, 'Lab')
    
    table_data = [headers]
    for row in data:
        table_row = [
            row['Name'],
            row['Registry Number'],
            str(row['Quantity']),
            row['Unit'],
            str(row['Minimum Quantity']),
            row['Location'],
            row['Notes']
        ]
        if not lab_code:
            table_row.insert(0, row.get('Lab', ''))
        table_data.append(table_row)
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_word(data, lab_code=None):
    """Generate Word document as a stream"""
    doc = Document()
    title_text = f"Lab Inventory Report - {lab_code}" if lab_code else "Full Inventory Report"
    doc.add_heading(title_text, 0)
    
    timestamp = format_timestamp(datetime.utcnow())
    doc.add_paragraph(f"Generated on: {timestamp.strftime('%Y-%m-%d %H:%M')}")
    
    headers = ['Name', 'Registry #', 'Quantity', 'Unit', 'Min Qty', 'Location', 'Notes']
    if not lab_code:
        headers.insert(0, 'Lab')
    
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header
    
    for row in data:
        row_cells = table.add_row().cells
        col = 0
        if not lab_code:
            row_cells[col].text = row.get('Lab', '')
            col += 1
        row_cells[col].text = row['Name']
        row_cells[col + 1].text = row['Registry Number']
        row_cells[col + 2].text = str(row['Quantity'])
        row_cells[col + 3].text = row['Unit']
        row_cells[col + 4].text = str(row['Minimum Quantity'])
        row_cells[col + 5].text = row['Location']
        row_cells[col + 6].text = row['Notes']
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


@bp.route('/')
@bp.route('/index')
def index():
    """
    Anasayfa. main/index.html render edilir.
    """
    return render_template('main/index.html', title='Home')


@bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """
    Basit bir Admin kontrol paneli örneği.
    """
    return render_template('admin/dashboard.html')


@bp.route('/user/profile')
@login_required
def user_profile():
    """
    Kullanıcının profil sayfası (placeholder).
    """
    return render_template('user/profile.html')


@bp.route('/protected-route')
@login_required
def protected_route():
    """
    Giriş yapmış kullanıcıların görebileceği korumalı route (placeholder).
    """
    return render_template('protected.html')


@bp.route('/admin-only')
@login_required
@admin_required
def admin_only():
    """
    Yalnızca admin rolüne sahip kullanıcıların erişebileceği bir sayfa (placeholder).
    """
    return render_template('admin.html')


@bp.route('/products')
@login_required
def products():
    """
    Tüm kullanıcıların görebileceği bir ürün listesi (placeholder).
    """
    return render_template('products.html')


@bp.route('/admin/manage-users')
@login_required
@admin_required
def manage_users():
    """
    Yalnızca adminlerin görebileceği kullanıcı yönetimi sayfası (placeholder).
    """
    return render_template('admin/manage_users.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Lists laboratories. Query param `lab=all` or `lab=<lab.code>`.
    """
    all_labs = Lab.get_predefined_labs()
    selected_lab_code = request.args.get('lab', 'all')

    if selected_lab_code == 'all':
        labs_to_show = all_labs
    else:
        selected_lab = next((lab for lab in all_labs if lab.code == selected_lab_code), None)
        if not selected_lab:
            selected_lab_code = 'all'
            labs_to_show = all_labs
        else:
            labs_to_show = [selected_lab]

    # Get sorted products for each lab
    lab_products = {}
    for lab in labs_to_show:
        lab_products[lab.id] = Product.get_sorted_products(lab.id)

    return render_template(
        'main/dashboard.html',
        title='Dashboard',
        labs=labs_to_show,
        all_labs=all_labs,
        selected_lab_code=selected_lab_code,
        lab_products=lab_products
    )


@bp.route('/product/add', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def add_product():
    form = ProductForm()
    labs = Lab.get_predefined_labs()

    if form.validate_on_submit():
        try:
            # Laboratuvar kontrolü
            selected_lab = Lab.query.get(form.lab_id.data)
            if not selected_lab:
                flash('Lütfen geçerli bir laboratuvar seçin.', 'error')
                return render_template('main/product_form.html', form=form, title='Ürün Ekle', labs=labs)

            # Sicil numarası kontrolü
            existing_product = Product.query.filter_by(registry_number=form.registry_number.data).first()
            if existing_product:
                flash('Bu sicil numarasına sahip bir ürün zaten mevcut.', 'error')
                return render_template('main/product_form.html', form=form, title='Ürün Ekle', labs=labs)

            # Konum bilgisi ayrıştırma
            loc_parts = form.location_number.data.split('-')
            if loc_parts[0] == 'workspace':
                location_type = 'workspace'
                location_number = None
                location_position = None
            else:
                location_type = 'cabinet'
                location_number = loc_parts[1]
                location_position = loc_parts[2]

            try:
                product = Product(
                    name=form.name.data,
                    registry_number=form.registry_number.data,
                    quantity=float(form.quantity.data),
                    unit=form.unit.data,
                    minimum_quantity=float(form.minimum_quantity.data),
                    location_type=location_type,
                    location_number=location_number,
                    location_position=location_position,
                    notes=form.notes.data,
                    lab_id=selected_lab.id
                )
            except ValueError as ve:
                current_app.logger.error(f"Validation error while creating product: {str(ve)}")
                flash(f'Doğrulama hatası: {str(ve)}', 'error')
                return render_template('main/product_form.html', form=form, title='Ürün Ekle', labs=labs)
            
            db.session.add(product)
            
            # Kullanıcı logu oluştur
            create_user_log(
                user=current_user,
                action_type='add',
                product=product,
                lab=selected_lab,
                quantity=product.quantity,
                notes=f"Yeni ürün eklendi: {product.name}"
            )

            try:
                db.session.commit()
            except Exception as dbe:
                db.session.rollback()
                current_app.logger.error(f"Database error while adding product: {str(dbe)}")
                flash(f'Veritabanı hatası: {str(dbe)}', 'error')
                return render_template('main/product_form.html', form=form, title='Ürün Ekle', labs=labs)

            # WebSocket bildirimi gönder
            notify_inventory_update(product.id, 'add', {
                'name': product.name,
                'registry_number': product.registry_number,
                'quantity': product.quantity,
                'lab_id': product.lab_id
            })

            flash(f'Ürün "{product.name}" başarıyla eklendi!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error while adding product: {str(e)}")
            flash(f'Beklenmeyen hata: {str(e)}', 'error')
            return render_template('main/product_form.html', form=form, title='Ürün Ekle', labs=labs)

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')

    return render_template('main/product_form.html', form=form, title='Ürün Ekle', labs=labs)


@bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per hour")
def edit_product(id):
    """
    Var olan ürünün düzenlenmesi (global route).
    """
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    labs = Lab.get_predefined_labs()

    # Mevcut product'ın konumu form field'ına set edelim
    if product.location_type == 'workspace':
        form.location_number.data = 'workspace'
    else:
        form.location_number.data = f"cabinet-{product.location_number}-{product.location_position}"

    # Lab dropdown default olarak product.lab_id
    form.lab_id.data = product.lab_id

    if form.validate_on_submit():
        try:
            selected_lab = Lab.query.get(form.lab_id.data)
            if not selected_lab:
                flash('Please select a valid laboratory.', 'error')
                return render_template('main/product_form.html', form=form, title='Edit Product', labs=labs)

            # Save old quantity for comparison
            old_quantity = product.quantity

            # Update product fields
            loc_parts = form.location_number.data.split('-')
            if loc_parts[0] == 'workspace':
                product.location_type = 'workspace'
                product.location_number = None
                product.location_position = None
            else:
                product.location_type = 'cabinet'
                product.location_number = loc_parts[1]
                product.location_position = loc_parts[2]

            product.name = form.name.data
            product.registry_number = form.registry_number.data
            product.quantity = form.quantity.data
            product.unit = form.unit.data
            product.minimum_quantity = form.minimum_quantity.data
            product.notes = form.notes.data
            product.lab_id = selected_lab.id

            # Check stock level and notify if necessary
            stock_level = product.check_stock_level()
            if stock_level in ['low', 'out']:
                notify_stock_alert(product, stock_level)

            # User log for quantity change
            if old_quantity != product.quantity:
                diff = product.quantity - old_quantity
                create_user_log(
                    user=current_user,
                    action_type='edit',
                    product=product,
                    lab=selected_lab,
                    quantity=diff,
                    notes=f"Updated quantity from {old_quantity} to {product.quantity}"
                )

            db.session.commit()

            # Notify via WebSocket
            notify_inventory_update(product.id, 'edit', {
                'name': product.name,
                'quantity': product.quantity,
                'lab_id': product.lab_id
            })

            flash('Product updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'error')

    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')

    return render_template('main/product_form.html', form=form, title='Edit Product', labs=labs)


@bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
@limiter.limit("10 per hour")
def delete_product(id):
    """
    Ürün silme işlemi (admin).
    """
    try:
        product = Product.query.get_or_404(id)

        create_user_log(
            user=current_user,
            action_type='delete',
            product=product,
            lab=product.lab,
            quantity=-product.quantity,  # Silinen miktar kaydı
            notes=f"Deleted product {product.name}"
        )

        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product. Please try again.', 'error')

    return redirect(url_for('main.dashboard'))


@bp.route('/product/<int:product_id>/transfer', methods=['GET', 'POST'])
@login_required
@limiter.limit("20 per hour")
def transfer_product(product_id):
    """Transfer a product between labs"""
    # First get the source product with its lab
    source_product = Product.query.join(Lab).filter(Product.id == product_id).first_or_404()
    
    if not source_product.lab:
        flash('Error: Source product has no associated laboratory.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get available destination labs (excluding source lab)
    destination_labs = Lab.query.filter(Lab.id != source_product.lab_id).all()
    if not destination_labs:
        flash('No available destination laboratories for transfer.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = TransferForm(source_lab_id=source_product.lab_id, max_quantity=source_product.quantity)
    form.destination_lab_id.choices = [(lab.id, f"{lab.code} - {lab.description}") for lab in destination_labs]

    if form.validate_on_submit():
        target_lab_id = form.destination_lab_id.data
        transfer_quantity = form.quantity.data
        notes = form.notes.data

        try:
            # Validate destination lab exists
            destination_lab = Lab.query.get(target_lab_id)
            if not destination_lab:
                flash('Selected destination laboratory does not exist.', 'danger')
                return render_template('main/transfer_form.html', title='Transfer Product', form=form, product=source_product)

            # Check for existing product in destination lab with cleaned registry number
            clean_registry = source_product.registry_number.strip()
            target_product_exists = Product.query.filter_by(
                lab_id=target_lab_id,
                registry_number=clean_registry
            ).first()

            # Validate transfer quantity
            if transfer_quantity > source_product.quantity:
                flash('Transfer quantity cannot exceed available quantity!', 'danger')
                return render_template('main/transfer_form.html', title='Transfer Product', form=form, product=source_product)
                
            if transfer_quantity <= 0:
                flash('Transfer quantity must be positive!', 'danger')
                return render_template('main/transfer_form.html', title='Transfer Product', form=form, product=source_product)

            with db.session.begin_nested():
                if target_product_exists:
                    target_product_exists.quantity += transfer_quantity
                else:
                    target_product_exists = Product(
                        name=source_product.name,
                        registry_number=clean_registry,  # Use cleaned registry number
                        quantity=transfer_quantity,
                        unit=source_product.unit,
                        minimum_quantity=source_product.minimum_quantity,
                        location_type='workspace',
                        location_number=None,
                        location_position=None,
                        notes=notes or source_product.notes,
                        lab_id=target_lab_id
                    )
                    db.session.add(target_product_exists)

                source_product.quantity -= transfer_quantity

                # Use safe lab references for logs
                transfer_log = TransferLog(
                    product_id=source_product.id,
                    source_lab_id=source_product.lab_id,
                    destination_lab_id=target_lab_id,
                    quantity=transfer_quantity,
                    notes=f"Transferred from {source_product.lab.code} to {destination_lab.code}",
                    created_by_id=current_user.id
                )
                db.session.add(transfer_log)

                create_user_log(
                    user=current_user,
                    action_type='transfer',
                    product=source_product,
                    lab=source_product.lab,
                    quantity=-transfer_quantity,
                    notes=f"Transferred {transfer_quantity} {source_product.unit} to {destination_lab.code}"
                )
                create_user_log(
                    user=current_user,
                    action_type='transfer',
                    product=target_product_exists,
                    lab=destination_lab,
                    quantity=transfer_quantity,
                    notes=f"Received {transfer_quantity} {source_product.unit} from {source_product.lab.code}"
                )

                db.session.commit()

            notify_inventory_update(source_product.id, 'transfer', {
                'name': source_product.name,
                'quantity': source_product.quantity,
                'source_lab': source_product.lab_id,
                'destination_lab': target_lab_id
            })

            flash('Product transferred successfully!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error during transfer: {str(e)}', 'danger')
            return render_template('main/transfer_form.html', title='Transfer Product', form=form, product=source_product)

    return render_template('main/transfer_form.html', title='Transfer Product', form=form, product=source_product)


#######################################################################
#  - - -  BU İKİ ROUTE LAB-ID BAZLI DÜZENLEME/SİLME İSTEYENLER İÇİN - -
#######################################################################

@bp.route('/lab/<int:lab_id>/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lab_product(lab_id, product_id):
    """
    Belirli laboratuvardaki (lab_id) ürünü (product_id) düzenleme.
    """
    lab = Lab.query.get_or_404(lab_id)
    product = Product.query.filter_by(id=product_id, lab_id=lab_id).first_or_404()

    form = ProductForm(obj=product)
    # Sadece bu lab'ı dropdown'da göstermek istiyorsanız:
    form.lab_id.choices = [(lab.id, f"{lab.code} - {lab.description}")]
    form.lab_id.data = lab.id

    # Konum set et
    if product.location_type == 'workspace':
        form.location_number.data = 'workspace'
    else:
        form.location_number.data = f"cabinet-{product.location_number}-{product.location_position}"

    if form.validate_on_submit():
        try:
            old_quantity = product.quantity

            loc_parts = form.location_number.data.split('-')
            if loc_parts[0] == 'workspace':
                product.location_type = 'workspace'
                product.location_number = None
                product.location_position = None
            else:
                product.location_type = 'cabinet'
                product.location_number = loc_parts[1]
                product.location_position = loc_parts[2]

            product.name = form.name.data
            product.registry_number = form.registry_number.data
            product.quantity = form.quantity.data
            product.unit = form.unit.data
            product.minimum_quantity = form.minimum_quantity.data
            product.notes = form.notes.data
            # lab_id sabit: product.lab_id = lab.id

            # Miktar değiştiyse user log
            if old_quantity != product.quantity:
                diff = product.quantity - old_quantity
                create_user_log(
                    user=current_user,
                    action_type='edit',
                    product=product,
                    lab=lab,
                    quantity=diff,
                    notes="Edited product quantity"
                )

            db.session.commit()
            flash(f'Product in {lab.code} updated successfully!', 'success')
            return redirect(url_for('main.dashboard', lab=lab.code))

        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'error')

    return render_template('main/product_form.html', form=form,
                           title=f"Edit Product in {lab.code}",
                           labs=[lab])


@bp.route('/lab/<int:lab_id>/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_lab_product(lab_id, product_id):
    """
    Belirli laboratuvardaki ürünü silme (admin).
    """
    try:
        lab = Lab.query.get_or_404(lab_id)
        product = Product.query.filter_by(id=product_id, lab_id=lab_id).first_or_404()

        create_user_log(
            user=current_user,
            action_type='delete',
            product=product,
            lab=lab,
            quantity=-product.quantity,
            notes=f"Deleted product {product.name} from lab {lab.code}"
        )

        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product.name}" deleted successfully from {lab.code}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product. Please try again.', 'error')

    return redirect(url_for('main.dashboard', lab=lab.code))


#######################################################################
#  TRANSFER ROUTE
#######################################################################

@bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_between_labs():
    """
    Transfer formu: Source Lab -> Destination Lab.
    """
    form = TransferForm()
    form.source_lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    form.destination_lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    form.product_id.choices = [(p.id, f"{p.name} ({p.registry_number})") for p in Product.query.all()]

    if form.validate_on_submit():
        source_lab_id = form.source_lab_id.data
        destination_lab_id = form.destination_lab_id.data

        # Validate source and destination labs exist
        source_lab = Lab.query.get(source_lab_id)
        destination_lab = Lab.query.get(destination_lab_id)
        
        if not source_lab or not destination_lab:
            flash('Invalid source or destination laboratory.', 'error')
            return redirect(url_for('main.transfer_between_labs'))

        if source_lab_id == destination_lab_id:
            flash('Source and destination labs cannot be the same.', 'error')
            return redirect(url_for('main.transfer_between_labs'))

        try:
            db.session.begin_nested()

            # Validate product exists and belongs to source lab
            product = Product.query.get_or_404(form.product_id.data)
            if not product or product.lab_id != source_lab_id:
                flash('Selected product does not belong to the source lab.', 'error')
                db.session.rollback()
                return redirect(url_for('main.transfer_between_labs'))

            transfer_qty = form.quantity.data
            if product.quantity < transfer_qty:
                flash('Insufficient quantity in the source lab.', 'error')
                db.session.rollback()
                return redirect(url_for('main.transfer_between_labs'))

            # Kaynaktan düş
            old_quantity = product.quantity
            product.quantity = old_quantity - transfer_qty
            db.session.flush()  # henüz commit değil

            # Hedef lab'da aynı registry_number varsa ekle, yoksa yeni oluştur
            dest_product = Product.query.filter_by(registry_number=product.registry_number, lab_id=destination_lab_id).first()
            if dest_product:
                dest_product.quantity += transfer_qty
            else:
                dest_product = Product(
                    name=product.name,
                    registry_number=product.registry_number,
                    quantity=transfer_qty,
                    unit=product.unit,
                    minimum_quantity=product.minimum_quantity,
                    location_type='workspace',
                    location_number=None,
                    location_position=None,
                    notes=product.notes,
                    lab_id=destination_lab_id
                )
                db.session.add(dest_product)

            # Transfer Log - using safe lab codes
            transfer_log = TransferLog(
                product_id=product.id,
                source_lab_id=source_lab_id,
                destination_lab_id=destination_lab_id,
                quantity=transfer_qty,
                notes=f"Transferred from {source_lab.code} to {destination_lab.code}",
                created_by_id=current_user.id
            )
            db.session.add(transfer_log)

            # UserLog (source) - using safe lab codes
            create_user_log(
                user=current_user,
                action_type='transfer',
                product=product,
                lab=source_lab,
                quantity=-transfer_qty,
                notes=f"Transferred out {transfer_qty} from {source_lab.code} to {destination_lab.code}"
            )
            # UserLog (destination) - using safe lab codes
            create_user_log(
                user=current_user,
                action_type='transfer',
                product=dest_product,
                lab=destination_lab,
                quantity=transfer_qty,
                notes=f"Received {transfer_qty} from {source_lab.code}"
            )

            db.session.commit()

            notify_inventory_update(product.id, 'transfer', {
                'name': product.name,
                'quantity': product.quantity,
                'source_lab': source_lab_id,
                'destination_lab': destination_lab_id
            })

            flash('Transfer completed successfully!', 'success')
            return redirect(url_for('main.dashboard'))

        except ConcurrencyError:
            db.session.rollback()
            flash('Transfer failed: Product was modified by another user. Please try again.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error processing transfer. Please try again.', 'error')

    return render_template('main/transfer_form.html', form=form, title='Transfer Product')


#######################################################################
#  - - - - - - -  EXPORT ROTALARI (PDF / XLSX / DOCX) - - - - - - - - -
#######################################################################

@bp.route('/export/<lab_code>/<format>')
@login_required
@limiter.limit("10 per minute")
def export_lab(lab_code, format):
    """Export lab inventory with streaming response"""
    lab = Lab.query.filter_by(code=lab_code).first_or_404()
    products = Product.query.filter_by(lab_id=lab.id)\
        .options(joinedload(Product.lab))\
        .all()

    data = []
    for product in products:
        data.append({
            'Name': product.name,
            'Registry Number': product.registry_number,
            'Quantity': product.quantity,
            'Unit': product.unit,
            'Minimum Quantity': product.minimum_quantity,
            'Location': product.get_location_display(),
            'Notes': product.notes or ''
        })

    timestamp = format_timestamp(datetime.utcnow()).strftime('%Y%m%d_%H%M%S')
    filename = f"inventory_{lab.code}_{timestamp}"

    if format == 'xlsx':
        return Response(
            stream_with_context(generate_excel(data)),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.xlsx"
            }
        )

    elif format == 'pdf':
        return Response(
            stream_with_context(generate_pdf(data, lab.code)),
            mimetype='application/pdf',
            headers={
                "Content-Disposition": f"attachment; filename={filename}.pdf"
            }
        )

    elif format == 'docx':
        return Response(
            stream_with_context(generate_word(data, lab.code)),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={
                "Content-Disposition": f"attachment; filename={filename}.docx"
            }
        )

    return "Format not supported", 400

@bp.route('/export/all/<format>')
@login_required
@limiter.limit("5 per minute")
def export_all_labs(format):
    """Export all labs inventory with streaming response"""
    labs = Lab.query.all()
    all_data = []

    for lab in labs:
        products = Product.query.filter_by(lab_id=lab.id)\
            .options(joinedload(Product.lab))\
            .all()
            
        for product in products:
            all_data.append({
                'Lab': f"{lab.code} - {lab.description}",
                'Name': product.name,
                'Registry Number': product.registry_number,
                'Quantity': product.quantity,
                'Unit': product.unit,
                'Minimum Quantity': product.minimum_quantity,
                'Location': product.get_location_display(),
                'Notes': product.notes or ''
            })

    if not all_data:
        flash('No data available to export', 'warning')
        return redirect(url_for('main.dashboard'))

    timestamp = format_timestamp(datetime.utcnow()).strftime('%Y%m%d_%H%M%S')
    filename = f"full_inventory_{timestamp}"

    if format == 'xlsx':
        return Response(
            stream_with_context(generate_excel(all_data)),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}.xlsx"
            }
        )

    elif format == 'pdf':
        return Response(
            stream_with_context(generate_pdf(all_data)),
            mimetype='application/pdf',
            headers={
                "Content-Disposition": f"attachment; filename={filename}.pdf"
            }
        )

    elif format == 'docx':
        return Response(
            stream_with_context(generate_word(all_data)),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={
                "Content-Disposition": f"attachment; filename={filename}.docx"
            }
        )

    return "Format not supported", 400


#######################################################################
# USER ACTIVITY LOG GÖRÜNTÜLEME (ADMIN)
#######################################################################

@bp.route('/logs')
@login_required
@admin_required
def user_logs():
    """
    Kullanıcı aksiyon loglarını listeler (UserLog).
    """
    page = request.args.get('page', 1, type=int)
    per_page = 20
    logs = UserLog.query.order_by(UserLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('main/user_logs.html',
                           title='User Activity Logs',
                           logs=logs)


@bp.route('/search')
@login_required
@limiter.limit("30 per minute")
def search_products():
    """
    Ürün adı veya sicil numarasına göre arama yapar
    """
    query = request.args.get('q', '')
    lab_code = request.args.get('lab', 'all')
    
    if lab_code != 'all':
        lab = Lab.query.filter_by(code=lab_code).first_or_404()
        products = Product.search(query, lab.id)
    else:
        products = Product.search(query)
    
    return render_template('main/search_results.html',
                         title='Search Results',
                         query=query,
                         products=products,
                         selected_lab_code=lab_code)


@bp.route('/lab/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lab():
    """
    Yeni bir laboratuvar eklemek için form.
    """
    form = LabForm()
    if form.validate_on_submit():
        try:
            # Generate a code based on the lab name if not in predefined labs
            code = form.name.data.upper().replace(' ', '')[:20]
            
            lab = Lab(
                code=code,
                name=form.name.data,
                description=form.description.data,
                location=form.location.data,
                max_cabinets=8  # Default value
            )
            
            db.session.add(lab)
            db.session.commit()
            
            flash(f'Laboratory "{lab.name}" has been added successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding laboratory. Please try again.', 'error')
            
    return render_template('main/lab_form.html', form=form, title='Add Laboratory')
