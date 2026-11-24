"""Products: public list/search, admin write."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_admin
from ..models import Category, Product, User
from ..schemas import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


def to_out(product: Product) -> ProductOut:
    out = ProductOut.model_validate(product)
    out.category_name = product.category.name if product.category else None
    return out


@router.get("", response_model=list[ProductOut])
def list_products(
    q: str | None = Query(default=None, description="Search by name"),
    category_id: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    return [to_out(p) for p in query.order_by(Product.id).offset(skip).limit(limit).all()]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return to_out(product)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    if not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=400, detail="Category not found")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return to_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    if data.category_id and not db.query(Category).filter(Category.id == data.category_id).first():
        raise HTTPException(status_code=400, detail="Category not found")
    db.commit()
    db.refresh(product)
    return to_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
