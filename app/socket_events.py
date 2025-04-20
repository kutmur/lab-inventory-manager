# app/socket_events.py

from flask_socketio import emit, disconnect
from flask_login import current_user
from flask import current_app
from app.extensions import socketio
import functools

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
            return False
        return f(*args, **kwargs)
    return wrapped

@socketio.on('connect')
@authenticated_only
def handle_connect():
    """Client bağlantı olayı"""
    emit('status', {'msg': f'{current_user.username} connected'})
    current_app.logger.info(f'Client connected: {current_user.username}')

@socketio.on('disconnect')
def handle_disconnect():
    """Client bağlantı kopması olayı"""
    if current_user.is_authenticated:
        emit('status', {'msg': f'{current_user.username} disconnected'})
        current_app.logger.info(f'Client disconnected: {current_user.username}')

def notify_inventory_update(product_id, action, data):
    """
    Envanter değişikliklerini bildirir
    Args:
        product_id: Değişen ürünün ID'si
        action: 'add', 'edit', 'delete', veya 'transfer'
        data: Değişiklik detayları
    """
    try:
        payload = {
            'product_id': product_id,
            'action': action,
            'data': data,
            'user': current_user.username if current_user else 'System'
        }
        socketio.emit('inventory_update', payload)
    except Exception as e:
        current_app.logger.error(f"SocketIO inventory_update error: {str(e)}")
        # Don't re-raise - notification failure shouldn't break the main flow

def notify_stock_alert(product, level):
    """
    Stok seviyesi uyarılarını bildirir
    Args:
        product: Product model instance
        level: 'low' veya 'out'
    """
    try:
        payload = {
            'product_id': product.id,
            'product_name': product.name,
            'lab_code': product.lab.code,
            'level': level,
            'quantity': product.quantity,
            'minimum': product.minimum_quantity
        }
        socketio.emit('stock_alert', payload)
    except Exception as e:
        current_app.logger.error(f"SocketIO stock_alert error: {str(e)}")
        # Don't re-raise - alert failure shouldn't break the main flow
