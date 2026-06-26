"""Sunum / demo için göstermelik mock veri oluşturucu.

Çalıştırma (proje kökünden):

    python -m server.seed_data            # veritabanı boşsa doldurur
    python -m server.seed_data --reset    # mevcut verileri silip yeniden oluşturur

Oluşturulan veriler gerçek API akışıyla birebir tutarlıdır:
- Kart kayıtları (müşteriler)
- Ürünler (renkli placeholder görsellerle)
- Bakiye yüklemeleri (topup işlemleri)
- Alışverişler (satış + satış kalemleri + purchase işlemleri, stok düşümü)
"""

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

from .database import SessionLocal, init_db
from .models import Card, Product, Sale, SaleItem, Transaction

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"


# (kod, ad, fiyat, stok, renk[hex])
PRODUCTS = [
    ("TS-001", "Beyaz Basic Tişört", 199.90, 60, "#0ea5e9"),
    ("TS-002", "Siyah Oversize Tişört", 229.90, 45, "#1f2937"),
    ("GM-010", "Slim Fit Gömlek", 449.50, 30, "#4f46e5"),
    ("KZ-100", "Slim Kot Pantolon", 699.00, 35, "#2563eb"),
    ("KZ-101", "Chino Pantolon", 549.00, 25, "#a16207"),
    ("SW-050", "Kapüşonlu Sweatshirt", 599.90, 32, "#7c3aed"),
    ("CK-200", "Deri Biker Ceket", 1899.00, 10, "#111827"),
    ("EL-300", "Yün Triko Kazak", 749.00, 20, "#b45309"),
    ("ET-400", "Yazlık Saten Elbise", 899.00, 18, "#db2777"),
    ("AY-500", "Spor Ayakkabı", 1299.00, 22, "#059669"),
    ("AK-600", "Hakiki Deri Kemer", 299.00, 50, "#92400e"),
    ("SP-700", "Beyzbol Şapkası", 249.90, 28, "#0891b2"),
]

# (uid, ad, soyad, e-posta, telefon)
CUSTOMERS = [
    ("A1B2C3D4", "Ahmet", "Yılmaz", "ahmet.yilmaz@example.com", "0532 100 10 01"),
    ("B2C3D4E5", "Ayşe", "Kaya", "ayse.kaya@example.com", "0533 100 10 02"),
    ("C3D4E5F6", "Mehmet", "Demir", "mehmet.demir@example.com", "0534 100 10 03"),
    ("D4E5F6A7", "Fatma", "Şahin", "fatma.sahin@example.com", "0535 100 10 04"),
    ("E5F6A7B8", "Mustafa", "Çelik", "mustafa.celik@example.com", "0536 100 10 05"),
    ("F6A7B8C9", "Zeynep", "Arslan", "zeynep.arslan@example.com", "0537 100 10 06"),
    ("1A2B3C4D", "Emre", "Doğan", "emre.dogan@example.com", "0538 100 10 07"),
    ("2B3C4D5E", "Elif", "Yıldız", "elif.yildiz@example.com", "0539 100 10 08"),
]

# Müşteri başına başlangıç bakiyesi yüklemesi
TOPUP_AMOUNTS = [2000.0, 3500.0, 5000.0, 1500.0, 4000.0, 2500.0, 6000.0, 3000.0]


def _generate_product_image(code: str, name: str, color: str) -> str | None:
    """Ürün için renkli bir placeholder PNG üretir, /uploads yolunu döndürür.

    Pillow kurulu değilse None döner (ürün görselsiz oluşturulur).
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    UPLOAD_DIR.mkdir(exist_ok=True)
    size = (400, 400)
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)

    # Hafif bir alt şerit (kart gibi dursun)
    draw.rectangle([0, 320, 400, 400], fill="#00000033")

    def _load_font(px):
        for candidate in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(candidate, px)
            except OSError:
                continue
        return ImageFont.load_default()

    code_font = _load_font(34)
    name_font = _load_font(26)

    draw.text((28, 28), code, fill="#ffffff", font=code_font)

    # Ürün adını sığması için satırlara böl
    words = name.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) > 18:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)

    y = 335
    for line in lines[:2]:
        draw.text((28, y), line, fill="#ffffff", font=name_font)
        y += 30

    filename = f"seed_{code.lower().replace('-', '_')}.png"
    dest = UPLOAD_DIR / filename
    img.save(dest, "PNG")
    return f"/uploads/{filename}"


def _reset(db):
    db.query(SaleItem).delete()
    db.query(Sale).delete()
    db.query(Transaction).delete()
    db.query(Card).delete()
    db.query(Product).delete()
    db.commit()


def seed(reset: bool = False):
    init_db()
    db = SessionLocal()
    random.seed(42)

    try:
        existing = db.query(Product).count() + db.query(Card).count()
        if existing and not reset:
            print(
                f"Veritabanında zaten {existing} kayıt var. "
                "Yeniden oluşturmak için: python -m server.seed_data --reset"
            )
            return
        if reset:
            _reset(db)
            print("Mevcut veriler temizlendi.")

        now = datetime.utcnow()

        # --- Ürünler ---
        products = []
        images_ok = True
        for code, name, price, stock, color in PRODUCTS:
            image_path = _generate_product_image(code, name, color)
            if image_path is None:
                images_ok = False
            product = Product(
                product_code=code,
                name=name,
                price=price,
                stock=stock,
                image_path=image_path,
                created_at=now - timedelta(days=random.randint(20, 40)),
            )
            db.add(product)
            products.append(product)
        db.flush()
        print(f"{len(products)} ürün oluşturuldu.")
        if not images_ok:
            print("  (Pillow kurulu değil; ürünler görselsiz oluşturuldu. "
                  "Görseller için: pip install pillow)")

        # --- Müşteriler + bakiye yüklemeleri ---
        cards = []
        for (uid, first, last, email, phone), topup in zip(CUSTOMERS, TOPUP_AMOUNTS):
            created = now - timedelta(days=random.randint(25, 45))
            card = Card(
                card_uid=uid,
                first_name=first,
                last_name=last,
                email=email,
                phone=phone,
                balance=topup,
                created_at=created,
            )
            db.add(card)
            db.flush()
            db.add(
                Transaction(
                    card_id=card.id,
                    type="topup",
                    amount=topup,
                    created_at=created + timedelta(minutes=5),
                )
            )
            cards.append(card)
        db.flush()
        print(f"{len(cards)} müşteri ve bakiye yüklemesi oluşturuldu.")

        # --- Alışverişler ---
        sale_count = 0
        for card in cards:
            num_sales = random.randint(1, 4)
            for _ in range(num_sales):
                basket_size = random.randint(1, 3)
                chosen = random.sample(products, basket_size)
                items = []
                total = 0.0
                for product in chosen:
                    qty = random.randint(1, 2)
                    if product.stock < qty:
                        continue
                    items.append((product, qty, product.price))
                    total += product.price * qty

                if not items or card.balance < total:
                    continue

                sale_date = card.created_at + timedelta(
                    days=random.randint(1, 25),
                    hours=random.randint(9, 20),
                    minutes=random.randint(0, 59),
                )
                if sale_date > now:
                    sale_date = now - timedelta(hours=random.randint(1, 48))

                sale = Sale(card_id=card.id, total_amount=total, created_at=sale_date)
                db.add(sale)
                db.flush()
                for product, qty, unit_price in items:
                    product.stock -= qty
                    db.add(
                        SaleItem(
                            sale_id=sale.id,
                            product_id=product.id,
                            quantity=qty,
                            unit_price=unit_price,
                        )
                    )
                card.balance -= total
                db.add(
                    Transaction(
                        card_id=card.id,
                        type="purchase",
                        amount=total,
                        created_at=sale_date,
                    )
                )
                sale_count += 1

        db.commit()
        print(f"{sale_count} alışveriş (satış) oluşturuldu.")
        print("\nDemo verileri hazır! Sunucuyu başlatıp istemciden görüntüleyebilirsiniz.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo/mock veri oluşturucu")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Mevcut tüm verileri silip yeniden oluşturur",
    )
    args = parser.parse_args()
    seed(reset=args.reset)
