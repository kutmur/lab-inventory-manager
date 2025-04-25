# app/socket_events.py

from flask_socketio import emit, disconnect
from flask_login import current_user
from flask import current_app
from app.extensions import socketio, db
import functools
import time
from redis.exceptions import RedisError

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
            return False
        return f(*args, **kwargs)
    return wrapped

def handle_redis_error(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except RedisError as e:
            current_app.logger.error(f"Redis error in socket event: {str(e)}")
            # Fallback to direct emit if Redis fails
            try:
                return f(*args, **kwargs, _direct=True)
            except Exception as e2:
                current_app.logger.error(f"Direct emit also failed: {str(e2)}")
        except Exception as e:
            current_app.logger.error(f"Unexpected error in socket event: {str(e)}")
        return None
    return wrapped

@socketio.on('connect')
@authenticated_only
def handle_connect():
    """Client connection event with retry mechanism"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            emit('status', {'msg': f'{current_user.username} connected'})
            current_app.logger.info(f'Client connected: {current_user.username}')
            return True
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                current_app.logger.error(f'Failed to handle connection after {max_retries} attempts: {str(e)}')
                return False
            time.sleep(0.5)  # Short delay before retry

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnection event"""
    if current_user.is_authenticated:
        try:
            emit('status', {'msg': f'{current_user.username} disconnected'})
            current_app.logger.info(f'Client disconnected: {current_user.username}')
        except Exception as e:
            current_app.logger.error(f'Error handling disconnect: {str(e)}')

@handle_redis_error
def notify_inventory_update(product_id, action, data, _direct=False):
    """
    Notify inventory changes with Redis error handling and direct fallback
    Args:
        product_id: Changed product's ID
        action: 'add', 'edit', 'delete', or 'transfer'
        data: Change details
        _direct: Internal flag for direct emit fallback
    """
    try:
        payload = {
            'product_id': product_id,
            'action': action,
            'data': data,
            'user': current_user.username if current_user else 'System'
        }
        
        if _direct:
            # Direct emit without Redis
            socketio.emit('inventory_update', payload)
        else:
            # Normal emit through Redis
            socketio.emit('inventory_update', payload)
            
    except Exception as e:
        current_app.logger.error(f"Error in notify_inventory_update: {str(e)}")
        db.session.rollback()  # Ensure database session is clean
        raise

@handle_redis_error
def notify_stock_alert(product, level, _direct=False):
    """
    Notify stock level alerts with Redis error handling
    Args:
        product: Product model instance
        level: 'low' or 'out'
        _direct: Internal flag for direct emit fallback
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
        
        if _direct:
            socketio.emit('stock_alert', payload)
        else:
            socketio.emit('stock_alert', payload)
            
    except Exception as e:
        current_app.logger.error(f"Error in notify_stock_alert: {str(e)}")
        db.session.rollback()
        raise
