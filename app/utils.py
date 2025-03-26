from app.models import UserLog
from app.extensions import db

def create_user_log(user, action_type, product, lab, quantity, notes=None):
    """
    Create a user action log entry
    """
    log = UserLog(
        user_id=user.id,
        action_type=action_type,
        product_id=product.id,
        lab_id=lab.id,
        quantity=quantity,
        notes=notes
    )
    db.session.add(log)
    return log 