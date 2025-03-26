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
    return render_template('main/index.html', title='Home')

@bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Only admins can access this route
    return render_template('admin/dashboard.html')

@bp.route('/user/profile')
@login_required
def user_profile():
    # Any logged-in user can access this route
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
    """Route accessible to all logged-in users"""
    return render_template('products.html')

@bp.route('/admin/manage-users')
@login_required
@admin_required
def manage_users():
    """Route accessible only to admin users"""
    return render_template('admin/manage_users.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    labs = Lab.query.all()
    return render_template('main/dashboard.html', title='Dashboard', labs=labs)

@bp.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    form.lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    
    if form.validate_on_submit():
        try:
            product = Product(
                name=form.name.data,
                registry_number=form.registry_number.data,
                quantity=form.quantity.data,
                unit=form.unit.data,
                minimum_quantity=form.minimum_quantity.data,
                location_in_lab=form.location_in_lab.data,
                notes=form.notes.data,
                lab_id=form.lab_id.data
            )
            db.session.add(product)
            db.session.flush()  # Get product.id
            
            # Create log entry
            create_user_log(
                user=current_user,
                action_type='add',
                product=product,
                lab=Lab.query.get(form.lab_id.data),
                quantity=form.quantity.data,
                notes=f"Added new product: {product.name}"
            )
            
            db.session.commit()

            # Notify connected clients
            notify_inventory_update(product.id, 'add', {
                'name': product.name,
                'registry_number': product.registry_number,
                'quantity': product.quantity,
                'lab_id': product.lab_id
            })

            flash('Product added successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding product. Please try again.', 'error')
    
    return render_template('main/product_form.html', form=form, title='Add Product')

@bp.route('/product/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    form.lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    
    if form.validate_on_submit():
        try:
            old_quantity = product.quantity
            product.name = form.name.data
            product.registry_number = form.registry_number.data
            product.quantity = form.quantity.data
            product.unit = form.unit.data
            product.minimum_quantity = form.minimum_quantity.data
            product.location_in_lab = form.location_in_lab.data
            product.notes = form.notes.data
            product.lab_id = form.lab_id.data
            
            if old_quantity != form.quantity.data:
                log = UserLog(
                    user_id=current_user.id,
                    product_id=product.id,
                    lab_id=form.lab_id.data,
                    action_type='edit',
                    quantity=form.quantity.data - old_quantity
                )
                db.session.add(log)
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'error')
    
    return render_template('main/product_form.html', form=form, title='Edit Product')

@bp.route('/product/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    try:
        product = Product.query.get_or_404(id)
        log = UserLog(
            user_id=current_user.id,
            product_id=product.id,
            lab_id=product.lab_id,
            action_type='delete',
            quantity=-product.quantity
        )
        db.session.add(log)
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
    form = TransferForm()
    form.source_lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    form.destination_lab_id.choices = [(lab.id, lab.name) for lab in Lab.query.all()]
    form.product_id.choices = [(p.id, f"{p.name} ({p.registry_number})") 
                             for p in Product.query.all()]
    
    if form.validate_on_submit():
        try:
            product = Product.query.get_or_404(form.product_id.data)
            
            # Start transaction
            db.session.begin_nested()
            
            try:
                # Update quantity with optimistic locking
                new_quantity = product.quantity - form.quantity.data
                product.update_quantity(new_quantity)
                
                # Create transfer log
                transfer = TransferLog(
                    product_id=product.id,
                    source_lab_id=form.source_lab_id.data,
                    destination_lab_id=form.destination_lab_id.data,
                    quantity=form.quantity.data,
                    notes=form.notes.data,
                    created_by_id=current_user.id
                )
                db.session.add(transfer)
                
                # Commit transaction
                db.session.commit()
                
                # Notify connected clients
                notify_inventory_update(product.id, 'transfer', {
                    'name': product.name,
                    'quantity': new_quantity,
                    'source_lab': form.source_lab_id.data,
                    'destination_lab': form.destination_lab_id.data
                })
                
                flash('Transfer completed successfully!', 'success')
                return redirect(url_for('main.dashboard'))
                
            except ConcurrencyError:
                db.session.rollback()
                flash('Transfer failed: Product was modified by another user. Please try again.', 'error')
                return redirect(url_for('main.transfer_product'))
                
        except Exception as e:
            db.session.rollback()
            flash('Error processing transfer. Please try again.', 'error')
    
    return render_template('main/transfer_form.html', form=form, title='Transfer Product')

@bp.route('/lab/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lab():
    form = LabForm()
    if form.validate_on_submit():
        lab = Lab(
            name=form.name.data,
            description=form.description.data,
            location=form.location.data
        )
        db.session.add(lab)
        db.session.commit()
        flash('Laboratory added successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('main/lab_form.html', form=form, title='Add Laboratory')

@bp.route('/logs')
@login_required
@admin_required
def user_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of logs per page
    
    logs = UserLog.query.order_by(UserLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('main/user_logs.html', 
                         title='User Activity Logs',
                         logs=logs)

@bp.route('/export/pdf')
@login_required
def export_pdf():
    try:
        # Create a buffer for the PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Lab Inventory Report", styles['Title']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        
        # Create table data
        data = [['Lab', 'Registry #', 'Product Name', 'Quantity', 'Unit', 'Location']]
        for lab in Lab.query.all():
            for product in lab.products:
                data.append([
                    lab.name,
                    product.registry_number,
                    product.name,
                    str(product.quantity),
                    product.unit,
                    product.location_in_lab or ''
                ])
        
        # Create and style the table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return send_file(
            buffer,
            download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"PDF generation error: {str(e)}")
        return "Error generating PDF", 500

@bp.route('/export/word')
@login_required
def export_word():
    try:
        # Create document
        doc = Document()
        doc.add_heading('Lab Inventory Report', 0)
        doc.add_paragraph(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        
        # Add table
        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        header_cells = table.rows[0].cells
        headers = ['Lab', 'Registry #', 'Product Name', 'Quantity', 'Unit', 'Location']
        for i, header in enumerate(headers):
            header_cells[i].text = header
        
        # Add data rows
        for lab in Lab.query.all():
            for product in lab.products:
                row_cells = table.add_row().cells
                row_cells[0].text = lab.name
                row_cells[1].text = product.registry_number
                row_cells[2].text = product.name
                row_cells[3].text = str(product.quantity)
                row_cells[4].text = product.unit
                row_cells[5].text = product.location_in_lab or ''
        
        # Save to buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
    except Exception as e:
        current_app.logger.error(f"Word document generation error: {str(e)}")
        return "Error generating Word document", 500

@bp.route('/export/excel')
@login_required
def export_excel():
    try:
        # Create data for DataFrame
        data = []
        for lab in Lab.query.all():
            for product in lab.products:
                data.append({
                    'Lab': lab.name,
                    'Registry #': product.registry_number,
                    'Product Name': product.name,
                    'Quantity': product.quantity,
                    'Unit': product.unit,
                    'Location': product.location_in_lab or '',
                    'Minimum Quantity': product.minimum_quantity,
                    'Notes': product.notes or ''
                })
        
        if not data:
            flash('No data available to export', 'warning')
            return redirect(url_for('main.dashboard'))

        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Inventory']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })
            
            # Format the header
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Adjust column width based on content
                max_length = max(df[value].astype(str).apply(len).max(), len(value))
                worksheet.set_column(col_num, col_num, max_length + 2)
        
        output.seek(0)
        
        return send_file(
            output,
            download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        current_app.logger.error(f"Excel generation error: {str(e)}")
        flash('Error generating Excel file. Please try again.', 'error')
        return redirect(url_for('main.dashboard')) 