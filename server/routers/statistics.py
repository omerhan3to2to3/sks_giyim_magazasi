from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Card, Product, Sale, SaleItem, Transaction
from ..schemas import CustomerPurchaseStat, ProductStat, StatisticsResponse

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/", response_model=StatisticsResponse)
def get_statistics(db: Session = Depends(get_db)):
    products = db.query(Product).all()

    product_stats = []
    for product in products:
        sold_query = (
            db.query(
                func.coalesce(func.sum(SaleItem.quantity), 0),
                func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price), 0.0),
            )
            .filter(SaleItem.product_id == product.id)
            .first()
        )
        total_sold = int(sold_query[0] or 0)
        total_revenue = float(sold_query[1] or 0.0)
        product_stats.append(
            ProductStat(
                product_id=product.id,
                product_code=product.product_code,
                name=product.name,
                price=product.price,
                stock=product.stock,
                total_sold=total_sold,
                total_revenue=total_revenue,
            )
        )

    customer_rows = (
        db.query(
            Card.card_uid,
            Card.first_name,
            Card.last_name,
            Product.product_code,
            Product.name,
            func.sum(SaleItem.quantity).label("qty"),
            func.sum(SaleItem.quantity * SaleItem.unit_price).label("spent"),
        )
        .join(Sale, Sale.card_id == Card.id)
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .join(Product, Product.id == SaleItem.product_id)
        .group_by(
            Card.card_uid,
            Card.first_name,
            Card.last_name,
            Product.product_code,
            Product.name,
        )
        .order_by(Card.last_name, Card.first_name, Product.name)
        .all()
    )

    customer_purchases = [
        CustomerPurchaseStat(
            card_uid=row.card_uid,
            customer_name=f"{row.first_name} {row.last_name}",
            product_code=row.product_code,
            product_name=row.name,
            quantity=int(row.qty or 0),
            total_spent=float(row.spent or 0.0),
        )
        for row in customer_rows
    ]

    total_sales_count = db.query(func.count(Sale.id)).scalar() or 0
    total_revenue = float(db.query(func.coalesce(func.sum(Sale.total_amount), 0.0)).scalar() or 0.0)
    total_topups = float(
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.type == "topup")
        .scalar()
        or 0.0
    )

    return StatisticsResponse(
        products=product_stats,
        customer_purchases=customer_purchases,
        total_sales_count=total_sales_count,
        total_revenue=total_revenue,
        total_topups=total_topups,
    )
