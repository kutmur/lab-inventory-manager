# app/main/routes.py

from flask import render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.main.forms import ProductForm, TransferForm, LabForm
from app.models import Product, Lab, TransferLog, UserLog
from app.extensions import db
from app.auth.decorators import admin_required
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from docx.shared import Inches
import pandas as pd
from app.utils import create_user_log
from app.socket_events import notify_inventory_update
from app.models.product import ConcurrencyError


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
    Admin kontrol paneli örneği.
    """
    return render_template('admin/dashboard.html')

@bp.route('/user/profile')
@login_required
def user_profile():
    return render_template('user/profile.html')

@bp.route('/protected-route')
@login_required
def protected_route():
    return render_template('protected.html')

@bp.route('/admin-only')
@login_required
@admin_required
def admin_only():
    return render_template('admin.html')

@bp.route('/products')
@login_required
def products():
    """
    Örnek: Tüm kullanıcıların görebileceği bir ürün listesi (şimdilik placeholder).
    """
    return render_template('products.html')

@bp.route('/admin/manage-users')
@login_required
@admin_required
def manage_users():
    """
    Sadece adminlerin görebileceği bir manage users sayfası. (placeholder)
    """
    return render_template('admin/manage_users.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Laboratuvarları listeler. Query param 'lab' = 'all' ya da lab.code olabilir.
    """
    # Tüm predefined labs’i getir
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
    
    return render_template(
        'main/dashboard.html', 
        title='Dashboard', 
        labs=labs_to_show,
        all_labs=all_labs,
        selected_lab_code=selected_lab_code
    )

@bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """
    Yeni bir ürün eklemek için form.
    Location bilgisi (workspace ya da cabinet-x-upper/lower) parse ediliyor.
    """
    form = ProductForm()
    if form.validate_on_submit():
        try:
            selected_lab = Lab.query.get(form.lab_id.data)
            if not selected_lab:
                flash('Please select a valid laboratory.', 'error')
                return render_template('main/product_form.html', form=form, title='Add Product')

            # Registry number uniqueness check
            if Product.query.filter_by(registry_number=form.registry_number.data).first():
                flash('A product with this registry number already exists.', 'error')
                return render_template('main/product_form.html', form=form, title='Add Product')

            # Konum parse
            loc_parts = form.location_number.data.split('-')
            if loc_parts[0] == 'workspace':
                location_type = 'workspace'
                location_number = None
                location_position = None
            else:
                # "cabinet-<num>-upper/lower" format
                location_type = 'cabinet'
                location_number = loc_parts[1]
                location_position = loc_parts[2]

            product = Product(
                name=form.name.data,
                registry_number=form.registry_number.data,
                quantity=form.quantity.data,
                unit=form.unit.data,
                minimum_quantity=form.minimum_quantity.data,
                location_type=location_type,
                location_number=location_number,
                location_position=location_position,
                notes=form.notes.data,
                lab_id=selected_lab.id
            )
            
            db.session.add(product)
            db.session.flush()

            # Log kaydı
            create_user_log(
                user=current_user,
                action_type='add',
                product=product,
                lab=selected_lab,
                quantity=product.quantity,
                notes=f"Added new product: {product.name}"
            )
            db.session.commit()

            # Socket.io notification
            notify_inventory_update(product.id, 'add', {
                'name': product.name,
                'registry_number': product.registry_number,
                'quantity': product.quantity,
                'lab_id': product.lab_id,
                'location_type': product.location_type,
                'location_number': product.location_number,
                'location_position': product.location_position
            })

            flash(f'Product "{product.name}" added successfully to {selected_lab.name}!', 'success')
            return redirect(url_for('main.dashboard'))
        except ValueError as ve:
            db.session.rollback()
            flash(f'Validation error: {str(ve)}', 'error')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding product: {str(e)}")
            flash('An error occurred while adding the product. Please try again.', 'error')

    # Form hataları (validate_on_submit değilse veya hata döndüyse)
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'error')

    return render_template('main/product_form.html', form=form, title='Add Product', labs=Lab.get_predefined_labs())

@bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    """
    Var olan ürün düzenlemesi.
    """
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    # Lab listesini set et
    form.lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]

    # location_number defaultu
    if product.location_type == 'workspace':
        form.location_number.data = 'workspace'
    else:
        form.location_number.data = f"cabinet-{product.location_number}-{product.location_position}"

    if form.validate_on_submit():
        try:
            old_quantity = product.quantity
            product.name = form.name.data
            product.registry_number = form.registry_number.data
            product.quantity = form.quantity.data
            product.unit = form.unit.data
            product.minimum_quantity = form.minimum_quantity.data

            # Lokasyon parse
            loc_parts = form.location_number.data.split('-')
            if loc_parts[0] == 'workspace':
                product.location_type = 'workspace'
                product.location_number = None
                product.location_position = None
            else:
                product.location_type = 'cabinet'
                product.location_number = loc_parts[1]
                product.location_position = loc_parts[2]

            product.notes = form.notes.data
            product.lab_id = form.lab_id.data

            # Miktar değiştiyse log
            if old_quantity != product.quantity:
                create_user_log(
                    user=current_user,
                    action_type='edit',
                    product=product,
                    lab=product.lab,
                    quantity=product.quantity - old_quantity,
                    notes="Edited product quantity"
                )

            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'error')

    return render_template('main/product_form.html', form=form, title='Edit Product', labs=Lab.get_predefined_labs())

@bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    """
    Ürün silme işlemi (admin).
    """
    try:
        product = Product.query.get_or_404(id)
        # Log
        create_user_log(
            user=current_user,
            action_type='delete',
            product=product,
            lab=product.lab,
            quantity=-product.quantity,
            notes=f"Deleted product {product.name}"
        )
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product. Please try again.', 'error')
    
    return redirect(url_for('main.dashboard'))

@bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_product():
    """
    Transfer formu. Source lab -> Destination lab.
    """
    form = TransferForm()
    form.source_lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    form.destination_lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    form.product_id.choices = [(p.id, f"{p.name} ({p.registry_number})") for p in Product.query.all()]

    if form.validate_on_submit():
        source_lab_id = form.source_lab_id.data
        destination_lab_id = form.destination_lab_id.data

        if source_lab_id == destination_lab_id:
            flash('Source and destination labs cannot be the same.', 'error')
            return redirect(url_for('main.transfer_product'))

        try:
            db.session.begin_nested()

            product = Product.query.get_or_404(form.product_id.data)
            if product.lab_id != source_lab_id:
                flash('Selected product does not belong to the source lab.', 'error')
                db.session.rollback()
                return redirect(url_for('main.transfer_product'))

            transfer_qty = form.quantity.data
            if product.quantity < transfer_qty:
                flash('Insufficient quantity in the source lab.', 'error')
                db.session.rollback()
                return redirect(url_for('main.transfer_product'))

            # Kaynaktan düş
            old_quantity = product.quantity
            product.quantity = old_quantity - transfer_qty
            db.session.flush()  # Veritabanına yaz ama commit etme

            # Hedef lab’da aynı registry_number varsa ekle, yoksa yeni oluştur
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

            # Transfer Log
            transfer_log = TransferLog(
                product_id=product.id,
                source_lab_id=source_lab_id,
                destination_lab_id=destination_lab_id,
                quantity=transfer_qty,
                notes=form.notes.data,
                created_by_id=current_user.id
            )
            db.session.add(transfer_log)

            # User Log (source)
            create_user_log(
                user=current_user,
                action_type='transfer',
                product=product,
                lab=product.lab,
                quantity=-transfer_qty,
                notes=f"Transferred out {transfer_qty} from {product.lab.code} to lab_id={destination_lab_id}"
            )
            # User Log (destination)
            create_user_log(
                user=current_user,
                action_type='transfer',
                product=dest_product,
                lab=dest_product.lab,
                quantity=transfer_qty,
                notes=f"Received {transfer_qty} from {product.lab.code}"
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


########################################################################
#  - - - - - - -  EXPORT ROTALARI (PDF/XLSX/DOCX) - - - - - - - -       #
########################################################################

@bp.route('/export/<lab_code>/<format>')
@login_required
def export_lab(lab_code, format):
    """
    Tek bir lab'ın envanterini PDF, Excel veya Word formatında döndürür.
    lab_code => Lab.code
    format => pdf / xlsx / docx
    """

    # Lab sorgula, yoksa 404
    lab = Lab.query.filter_by(code=lab_code).first_or_404()

    # Ürünleri çek
    products = Product.query.filter_by(lab_id=lab.id).all()

    # DataFrame için verileri hazırlayalım
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

    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"inventory_{lab.code}_{timestamp}"

    # 1) EXCEL
    if format == 'xlsx':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
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
        return send_file(
            output,
            download_name=f"{filename}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True
        )

    # 2) PDF
    elif format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(f"Lab Inventory Report - {lab.code}", styles['Title']))
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
            styles['Normal']
        ))

        table_data = [
            ['Name', 'Registry #', 'Quantity', 'Unit', 'Min Qty', 'Location', 'Notes']
        ]
        for row in data:
            table_data.append([
                row['Name'],
                row['Registry Number'],
                str(row['Quantity']),
                row['Unit'],
                str(row['Minimum Quantity']),
                row['Location'],
                row['Notes']
            ])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            download_name=f"{filename}.pdf",
            mimetype='application/pdf',
            as_attachment=True
        )

    # 3) DOCX
    elif format == 'docx':
        doc = Document()
        doc.add_heading(f"Lab Inventory Report - {lab.code}", 0)
        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        table = doc.add_table(rows=1, cols=7)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['Name', 'Registry #', 'Quantity', 'Unit', 'Min Qty', 'Location', 'Notes']
        for i, h in enumerate(headers):
            hdr_cells[i].text = h

        for row in data:
            row_cells = table.add_row().cells
            row_cells[0].text = row['Name']
            row_cells[1].text = row['Registry Number']
            row_cells[2].text = str(row['Quantity'])
            row_cells[3].text = row['Unit']
            row_cells[4].text = str(row['Minimum Quantity'])
            row_cells[5].text = row['Location']
            row_cells[6].text = row['Notes']

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return send_file(
            buffer,
            download_name=f"{filename}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True
        )

    else:
        return "Format not supported", 400


@bp.route('/export/all/<format>')
@login_required
def export_all_labs(format):
    """
    Tüm laboratuvarların envanterini PDF, Excel veya Word formatında döndürür.
    format => pdf / xlsx / docx
    """
    labs = Lab.query.all()
    all_data = []

    for lab in labs:
        products = Product.query.filter_by(lab_id=lab.id).all()
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

    # Boşsa uyarı
    if not all_data:
        flash('No data available to export', 'warning')
        return redirect(url_for('main.dashboard'))

    df = pd.DataFrame(all_data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"full_inventory_{timestamp}"

    # 1) XLSX
    if format == 'xlsx':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='All Labs', index=False)
            workbook = writer.book
            worksheet = writer.sheets['All Labs']
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
        return send_file(
            output,
            download_name=f"{filename}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True
        )

    # 2) PDF
    elif format == 'pdf':
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("All Labs Inventory Report", styles['Title']))
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
            styles['Normal']
        ))

        table_data = [
            ['Lab', 'Name', 'Registry #', 'Quantity', 'Unit', 'Min Qty', 'Location', 'Notes']
        ]
        for _, row in df.iterrows():
            table_data.append([
                row['Lab'],
                row['Name'],
                row['Registry Number'],
                str(row['Quantity']),
                row['Unit'],
                str(row['Minimum Quantity']),
                row['Location'],
                row['Notes']
            ])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            download_name=f"{filename}.pdf",
            mimetype='application/pdf',
            as_attachment=True
        )

    # 3) DOCX
    elif format == 'docx':
        doc = Document()
        doc.add_heading("All Labs Inventory Report", 0)
        doc.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        table = doc.add_table(rows=1, cols=8)
        table.style = 'Table Grid'
        hdr = table.rows[0].cells
        hdr[0].text = 'Lab'
        hdr[1].text = 'Name'
        hdr[2].text = 'Registry #'
        hdr[3].text = 'Quantity'
        hdr[4].text = 'Unit'
        hdr[5].text = 'Min Qty'
        hdr[6].text = 'Location'
        hdr[7].text = 'Notes'

        for _, row in df.iterrows():
            row_cells = table.add_row().cells
            row_cells[0].text = str(row['Lab'])
            row_cells[1].text = str(row['Name'])
            row_cells[2].text = str(row['Registry Number'])
            row_cells[3].text = str(row['Quantity'])
            row_cells[4].text = str(row['Unit'])
            row_cells[5].text = str(row['Minimum Quantity'])
            row_cells[6].text = str(row['Location'])
            row_cells[7].text = str(row['Notes'])

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return send_file(
            buffer,
            download_name=f"{filename}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True
        )

    else:
        return "Format not supported", 400


########################################################################
# Ek olarak, user_logs fonksiyonu da istersen buraya ekleyebilirsin:
########################################################################

@bp.route('/logs')
@login_required
@admin_required
def user_logs():
    """
    Kullanıcı aksiyon loglarını listeler. 
    """
    page = request.args.get('page', 1, type=int)
    per_page = 20
    logs = UserLog.query.order_by(UserLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('main/user_logs.html', 
                           title='User Activity Logs',
                           logs=logs)
