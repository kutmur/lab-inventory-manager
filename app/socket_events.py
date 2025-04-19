# app/socket_events.py

from flask_socketio import emit
from flask_login import current_user
from flask import current_app
from app.extensions import socketio

@socketio.on('connect')
def handle_connect():
    """Client bağlantı olayı"""
    if not current_user.is_authenticated:
        return False
    emit('status', {'msg': f'{current_user.username} connected'})
    current_app.logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """Client bağlantı kopması olayı"""
    if current_user.is_authenticated:
        emit('status', {'msg': f'{current_user.username} disconnected'})
    current_app.logger.info('Client disconnected')

def notify_inventory_update(product_id, action, data):
    """
    Envanter değişikliklerini bildirir
    Args:
        product_id: Değişen ürünün ID'si
        action: 'add', 'edit', 'delete', veya 'transfer'
        data: Değişiklik detayları
    """
    try:
        socketio.emit('inventory_update', {
            'product_id': product_id,
            'action': action,
            'data': data,
            'user': current_user.username if current_user else 'System'
        })
    except Exception as e:
        current_app.logger.error(f"SocketIO emit error: {str(e)}")

def notify_stock_alert(product, level):
    """
    Stok seviyesi uyarılarını bildirir
    Args:
        product: Product model instance
        level: 'low' veya 'out'
    """
    try:
        socketio.emit('stock_alert', {
            'product_id': product.id,
            'product_name': product.name,
            'lab_code': product.lab.code,
            'level': level,
            'quantity': product.quantity,
            'minimum': product.minimum_quantity
        })
    except Exception as e:
        current_app.logger.error(f"SocketIO stock alert error: {str(e)}")
