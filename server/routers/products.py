import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..schemas import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["products"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return [ProductResponse.model_validate(p) for p in products]


@router.post("/", response_model=ProductResponse)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    code = payload.product_code.strip()
    existing = db.query(Product).filter(Product.product_code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu ürün ID zaten mevcut.")

    product = Product(
        product_code=code,
        name=payload.name.strip(),
        price=payload.price,
        stock=payload.stock,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


@router.post("/with-image", response_model=ProductResponse)
async def create_product_with_image(
    product_code: str = Form(...),
    name: str = Form(...),
    price: float = Form(...),
    stock: int = Form(0),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    code = product_code.strip()
    existing = db.query(Product).filter(Product.product_code == code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu ürün ID zaten mevcut.")

    ext = Path(image.filename or "img.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / filename

    with dest.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    product = Product(
        product_code=code,
        name=name.strip(),
        price=price,
        stock=stock,
        image_path=f"/uploads/{filename}",
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    return ProductResponse.model_validate(product)
