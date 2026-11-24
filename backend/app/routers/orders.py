"""Orders: created from the cart. Stock is reduced at order time."""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_admin, get_current_user
from ..models import CartItem, Order, OrderItem, OrderStatus, Payment, PaymentMethod, PaymentStatus, User
from ..schemas import OrderCreate, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # bKash / Nagad need a transaction ID; COD must not have one.
    if data.payment_method in (PaymentMethod.BKASH, PaymentMethod.NAGAD):
        if not data.sender_number or not data.transaction_id:
            raise HTTPException(
                status_code=400,
                detail="sender_number and transaction_id are required for bKash / Nagad",
            )
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = Decimal("0")
    for item in cart_items:
        if item.quantity > item.product.stock:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {item.product.name}")
        total += item.product.price * item.quantity

    order = Order(
        user_id=user.id,
        status=OrderStatus.PENDING,
        total_amount=total,
        payment_method=data.payment_method,
        payment_status=PaymentStatus.PENDING,
        delivery_address=data.delivery_address,
        phone=data.phone,
    )
    db.add(order)
    db.flush()  # get order.id before adding items / payment

    for item in cart_items:
        db.add(OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.product.price))
        item.product.stock -= item.quantity

    db.add(
        Payment(
            order_id=order.id,
            method=data.payment_method,
            sender_number=data.sender_number,
            transaction_id=data.transaction_id,
            amount=total,
            status=PaymentStatus.PENDING,
        )
    )
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut])
def list_my_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).all()


@router.get("/all", response_model=list[OrderOut])
def list_all_orders(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.id.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not your order")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int, data: OrderStatusUpdate, _: User = Depends(get_current_admin), db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
