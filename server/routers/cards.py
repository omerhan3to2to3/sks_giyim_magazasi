from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Card, Transaction
from ..schemas import CardCreate, CardLookupResponse, CardResponse, TopUpRequest, TopUpResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/lookup/{card_uid}", response_model=CardLookupResponse)
def lookup_card(card_uid: str, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.card_uid == card_uid.upper()).first()
    if not card:
        return CardLookupResponse(exists=False, card=None)
    return CardLookupResponse(exists=True, card=CardResponse.model_validate(card))


@router.post("/register", response_model=CardResponse)
def register_card(payload: CardCreate, db: Session = Depends(get_db)):
    uid = payload.card_uid.upper().strip()
    existing = db.query(Card).filter(Card.card_uid == uid).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kart zaten kayıtlı.")

    card = Card(
        card_uid=uid,
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=payload.email.strip(),
        phone=payload.phone.strip(),
        balance=0.0,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return CardResponse.model_validate(card)


@router.post("/topup", response_model=TopUpResponse)
def topup_card(payload: TopUpRequest, db: Session = Depends(get_db)):
    uid = payload.card_uid.upper().strip()
    card = db.query(Card).filter(Card.card_uid == uid).first()
    if not card:
        raise HTTPException(status_code=404, detail="Kart bulunamadı. Önce kayıt yapın.")

    card.balance += payload.amount
    transaction = Transaction(card_id=card.id, type="topup", amount=payload.amount)
    db.add(transaction)
    db.commit()
    db.refresh(card)

    return TopUpResponse(
        card=CardResponse.model_validate(card),
        message=f"{payload.amount:.2f} TL yüklendi. Yeni bakiye: {card.balance:.2f} TL",
    )


@router.get("/", response_model=list[CardResponse])
def list_cards(db: Session = Depends(get_db)):
    cards = db.query(Card).order_by(Card.created_at.desc()).all()
    return [CardResponse.model_validate(c) for c in cards]
