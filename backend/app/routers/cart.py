"""Cart: one cart per customer, stored in the database."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import CartItem, Product, User
from ..schemas import CartAdd, CartItemOut, CartUpdate

router = APIRouter(prefix="/cart", tags=["cart"])


def to_out(item: CartItem) -> CartItemOut:
    return CartItemOut(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name,
        price=item.product.price,
        quantity=item.quantity,
        subtotal=item.product.price * item.quantity,
    )


@router.get("", response_model=list[CartItemOut])
def view_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    return [to_out(i) for i in items]


@router.post("", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(data: CartAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == data.product_id, Product.is_active.is_(True)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or inactive")
    if data.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock")
    item = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.product_id == data.product_id).first()
    if item:
        if item.quantity + data.quantity > product.stock:
            raise HTTPException(status_code=400, detail="Not enough stock")
        item.quantity += data.quantity
    else:
        item = CartItem(user_id=user.id, product_id=data.product_id, quantity=data.quantity)
        db.add(item)
    db.commit()
    db.refresh(item)
    return to_out(item)


@router.put("/{item_id}", response_model=CartItemOut)
def update_cart_item(item_id: int, data: CartUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if data.quantity > item.product.stock:
        raise HTTPException(status_code=400, detail="Not enough stock")
    item.quantity = data.quantity
    db.commit()
    db.refresh(item)
    return to_out(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == user.id).delete()
    db.commit()
