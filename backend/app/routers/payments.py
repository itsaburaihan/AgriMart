"""Payments: manual bKash / Nagad verification by the farmer (admin).

Flow: customer pays to the merchant number, submits sender number +
transaction ID with the order. Admin checks the bKash/Nagad app and
marks the payment verified or rejected here.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_admin, get_current_user
from ..models import Order, Payment, PaymentStatus, User
from ..schemas import PaymentInfoOut, PaymentOut, PaymentVerify

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/info", response_model=PaymentInfoOut)
def payment_info():
    """Merchant numbers the frontend shows at checkout."""
    return PaymentInfoOut(bkash_number=settings.bkash_number, nagad_number=settings.nagad_number)


@router.get("", response_model=list[PaymentOut])
def list_payments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role.value == "admin":
        return db.query(Payment).order_by(Payment.id.desc()).all()
    order_ids = [o.id for o in db.query(Order).filter(Order.user_id == user.id).all()]
    return db.query(Payment).filter(Payment.order_id.in_(order_ids)).order_by(Payment.id.desc()).all()


@router.get("/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if user.role.value != "admin" and payment.order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your payment")
    return payment


@router.patch("/{payment_id}/verify", response_model=PaymentOut)
def verify_payment(
    payment_id: int, data: PaymentVerify, _: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    if data.status == PaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Use verified or rejected, not pending")
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment.status = data.status
    payment.order.payment_status = data.status
    db.commit()
    db.refresh(payment)
    return payment
