from flask_socketio import emit
from flask_login import current_user
from app.extensions import socketio

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False
    emit('status', {'msg': f'{current_user.username} connected'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        emit('status', {'msg': f'{current_user.username} disconnected'}, broadcast=True)

def notify_inventory_update(product_id, action, data):
    """Emit inventory update event to all connected clients"""
    emit('inventory_update', {
        'product_id': product_id,
        'action': action,
        'data': data,
        'user': current_user.username
    }, broadcast=True, namespace='/') 