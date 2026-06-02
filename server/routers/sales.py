from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Card, Product, Sale, SaleItem, Transaction
from ..schemas import PurchaseRequest, PurchaseResponse

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("/purchase", response_model=PurchaseResponse)
def purchase(payload: PurchaseRequest, db: Session = Depends(get_db)):
    uid = payload.card_uid.upper().strip()
    card = db.query(Card).filter(Card.card_uid == uid).first()
    if not card:
        raise HTTPException(status_code=404, detail="Kart bulunamadı.")

    if not payload.items:
        raise HTTPException(status_code=400, detail="Sepet boş.")

    total = 0.0
    sale_items = []

    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: {item.product_id}")
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Yetersiz stok: {product.name} (Mevcut: {product.stock})",
            )
        line_total = product.price * item.quantity
        total += line_total
        sale_items.append((product, item.quantity, product.price))

    if card.balance < total:
        raise HTTPException(
            status_code=400,
            detail=f"Yetersiz bakiye. Gerekli: {total:.2f} TL, Mevcut: {card.balance:.2f} TL",
        )

    sale = Sale(card_id=card.id, total_amount=total)
    db.add(sale)
    db.flush()

    for product, quantity, unit_price in sale_items:
        product.stock -= quantity
        db.add(
            SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
            )
        )

    card.balance -= total
    db.add(Transaction(card_id=card.id, type="purchase", amount=total))
    db.commit()
    db.refresh(card)

    return PurchaseResponse(
        sale_id=sale.id,
        total_amount=total,
        remaining_balance=card.balance,
        message=f"Alışveriş tamamlandı. Toplam: {total:.2f} TL",
    )
