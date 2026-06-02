from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class CardCreate(BaseModel):
    card_uid: str
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


class CardResponse(BaseModel):
    id: int
    card_uid: str
    first_name: str
    last_name: str
    email: str
    phone: str
    balance: float
    created_at: datetime

    class Config:
        from_attributes = True


class CardLookupResponse(BaseModel):
    exists: bool
    card: Optional[CardResponse] = None


class TopUpRequest(BaseModel):
    card_uid: str
    amount: float = Field(gt=0)


class TopUpResponse(BaseModel):
    card: CardResponse
    message: str


class ProductCreate(BaseModel):
    product_code: str
    name: str
    price: float = Field(gt=0)
    stock: int = Field(default=0, ge=0)


class ProductResponse(BaseModel):
    id: int
    product_code: str
    name: str
    price: float
    image_path: Optional[str] = None
    stock: int
    created_at: datetime

    class Config:
        from_attributes = True


class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class PurchaseRequest(BaseModel):
    card_uid: str
    items: List[CartItemRequest]


class PurchaseResponse(BaseModel):
    sale_id: int
    total_amount: float
    remaining_balance: float
    message: str


class ProductStat(BaseModel):
    product_id: int
    product_code: str
    name: str
    price: float
    stock: int
    total_sold: int
    total_revenue: float


class CustomerPurchaseStat(BaseModel):
    card_uid: str
    customer_name: str
    product_code: str
    product_name: str
    quantity: int
    total_spent: float


class StatisticsResponse(BaseModel):
    products: List[ProductStat]
    customer_purchases: List[CustomerPurchaseStat]
    total_sales_count: int
    total_revenue: float
    total_topups: float
