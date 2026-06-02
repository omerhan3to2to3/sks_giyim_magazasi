import io
import threading
import urllib.request

import customtkinter as ctk
from PIL import Image

from client import theme as T
from .add_product_dialog import AddProductDialog


class ShoppingPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.products = []
        self.cart = {}
        self._rfid_callback = None
        self._awaiting_payment = False
        self._product_images = {}

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=T.PAD_PAGE, pady=(T.PAD_PAGE, 12))
        header.grid_columnconfigure(0, weight=1)

        title_block = T.build_page_header(header, "Alışveriş", "Ürünleri sepete ekleyin ve kartla ödeyin.")
        title_block.grid(row=0, column=0, sticky="w")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.grid(row=0, column=1, sticky="e")

        T.ghost_btn(btn_row, text="+ Ürün Ekle", width=130, command=self._open_add_product).pack(
            side="left", padx=(0, 10)
        )
        ctk.CTkButton(
            btn_row,
            text="Alışverişi Tamamla",
            width=170,
            height=40,
            corner_radius=T.RADIUS_SM,
            fg_color=T.SUCCESS,
            hover_color=T.SUCCESS_HOVER,
            font=T.font_body(13),
            command=self._start_checkout,
        ).pack(side="left")

        self.products_frame = ctk.CTkScrollableFrame(
            self,
            label_text="  Ürünler",
            fg_color=T.SURFACE,
            label_fg_color=T.SURFACE,
            label_text_color=T.TEXT,
            corner_radius=T.RADIUS_LG,
            border_width=1,
            border_color=T.BORDER,
        )
        self.products_frame.grid(row=1, column=0, sticky="nsew", padx=(T.PAD_PAGE, 8), pady=12)
        self.products_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.cart_frame = T.card(self)
        self.cart_frame.grid(row=1, column=1, sticky="nsew", padx=(8, T.PAD_PAGE), pady=12)
        self.cart_frame.grid_columnconfigure(0, weight=1)
        self.cart_frame.grid_rowconfigure(1, weight=1)

        cart_header = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        cart_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            cart_header,
            text="Sepet",
            font=T.font_section(),
            text_color=T.TEXT,
        ).pack(side="left")

        self.cart_count = ctk.CTkLabel(
            cart_header,
            text="0 ürün",
            font=T.font_small(12),
            text_color=T.TEXT_MUTED,
        )
        self.cart_count.pack(side="right")

        self.cart_list = ctk.CTkScrollableFrame(
            self.cart_frame,
            height=400,
            fg_color=T.SURFACE_ALT,
            corner_radius=T.RADIUS_SM,
        )
        self.cart_list.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)

        total_box = ctk.CTkFrame(self.cart_frame, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM)
        total_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 16))

        self.total_label = ctk.CTkLabel(
            total_box,
            text="Toplam: 0,00 ₺",
            font=T.font_stat(18),
            text_color=T.TEXT,
        )
        self.total_label.pack(padx=16, pady=14, anchor="w")

        self._build_checkout_popup()

    def _build_checkout_popup(self):
        self.checkout_overlay = ctk.CTkFrame(self, fg_color=("gray20", "gray10"), corner_radius=0)

        self.checkout_panel = T.card(self.checkout_overlay, width=360)
        self.checkout_panel.place(relx=0.5, rely=0.5, anchor="center")

        accent = ctk.CTkFrame(self.checkout_panel, height=4, fg_color=T.SUCCESS, corner_radius=0)
        accent.pack(fill="x")

        inner = ctk.CTkFrame(self.checkout_panel, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=T.PAD_CARD, pady=T.PAD_CARD)

        ctk.CTkLabel(
            inner,
            text="Ödeme",
            font=T.font_section(20),
            text_color=T.TEXT,
        ).pack(anchor="w")

        self.checkout_message = ctk.CTkLabel(
            inner,
            text="Kartınızı RFID okuyucuya okutunuz.",
            font=T.font_body(14),
            text_color=T.TEXT,
            wraplength=300,
            justify="left",
        )
        self.checkout_message.pack(anchor="w", pady=(12, 8))

        amount_box = ctk.CTkFrame(inner, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM)
        amount_box.pack(fill="x", pady=(4, 16))

        self.checkout_amount_label = ctk.CTkLabel(
            amount_box,
            text="Toplam ücret: 0,00 ₺",
            font=T.font_stat(22),
            text_color=T.SUCCESS,
        )
        self.checkout_amount_label.pack(padx=16, pady=14, anchor="w")

        ctk.CTkLabel(
            inner,
            text="Ödeme tamamlanana kadar bu pencere açık kalır.",
            font=T.font_small(11),
            text_color=T.TEXT_MUTED,
            wraplength=300,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkButton(
            inner,
            text="Alışverişi İptal Et",
            height=38,
            corner_radius=T.RADIUS_SM,
            fg_color="transparent",
            hover_color=T.SURFACE_ALT,
            border_width=1,
            border_color=T.DANGER,
            text_color=T.DANGER,
            font=T.font_body(13),
            command=self._cancel_checkout,
        ).pack(fill="x")

        self.checkout_overlay.place_forget()

    def _cart_total(self) -> float:
        return sum(i["product"]["price"] * i["quantity"] for i in self.cart.values())

    def _show_checkout_popup(self):
        total = self._cart_total()
        self.checkout_amount_label.configure(text=f"Toplam ücret: {total:.2f} ₺")
        self.checkout_message.configure(
            text="Kartınızı RFID okuyucuya okutunuz.",
            text_color=T.TEXT,
        )
        self.checkout_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.checkout_overlay.lift()

    def _hide_checkout_popup(self):
        self.checkout_overlay.place_forget()

    def _cancel_checkout(self):
        self._awaiting_payment = False
        self._hide_checkout_popup()

    def _update_checkout_popup_total(self):
        if not self._awaiting_payment:
            return
        total = self._cart_total()
        self.checkout_amount_label.configure(text=f"Toplam ücret: {total:.2f} ₺")

    def on_show(self):
        self._rfid_callback = self._handle_rfid
        self.app.register_rfid_callback(self._rfid_callback)
        self._awaiting_payment = False
        self._hide_checkout_popup()
        self._load_products()

    def on_hide(self):
        if self._rfid_callback:
            self.app.unregister_rfid_callback(self._rfid_callback)
        self._awaiting_payment = False
        self._hide_checkout_popup()

    def _load_products(self):
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.products_frame,
            text="Ürünler yükleniyor...",
            font=T.font_body(13),
            text_color=T.TEXT_MUTED,
        ).grid(row=0, column=0, padx=16, pady=24, sticky="w")

        def work():
            return self.app.api.list_products()

        def on_success(products):
            self.products = products
            self._render_products()

        def on_error(exc):
            self.app.show_error(str(exc))
            self.products = []
            self._render_products()

        self.app.run_in_background(work, on_success=on_success, on_error=on_error)

    def _render_products(self):
        for widget in self.products_frame.winfo_children():
            widget.destroy()

        if not self.products:
            ctk.CTkLabel(
                self.products_frame,
                text="Henüz ürün eklenmemiş.\nSağ üstten «Ürün Ekle» ile başlayın.",
                font=T.font_body(13),
                text_color=T.TEXT_MUTED,
                justify="left",
            ).grid(row=0, column=0, padx=16, pady=24, sticky="w")
            return

        for idx, product in enumerate(self.products):
            row, col = divmod(idx, 3)
            card = T.card(self.products_frame)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            img_wrap = ctk.CTkFrame(card, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM, width=148, height=148)
            img_wrap.pack(padx=12, pady=(12, 8))
            img_wrap.pack_propagate(False)

            img_label = ctk.CTkLabel(img_wrap, text="", width=140, height=140)
            img_label.place(relx=0.5, rely=0.5, anchor="center")
            self._load_product_image(product, img_label)

            ctk.CTkLabel(
                card,
                text=product["name"],
                font=T.font_body(14),
                text_color=T.TEXT,
                wraplength=160,
            ).pack(padx=12, pady=2)

            ctk.CTkLabel(
                card,
                text=f"{product['product_code']}  ·  {product['price']:.2f} ₺",
                text_color=T.TEXT_MUTED,
                font=T.font_small(12),
            ).pack(padx=12, pady=2)

            stock_color = T.SUCCESS if product["stock"] > 0 else T.DANGER
            ctk.CTkLabel(
                card,
                text=f"Stok: {product['stock']}",
                font=T.font_small(11),
                text_color=stock_color,
            ).pack(padx=12, pady=(0, 8))

            ctk.CTkButton(
                card,
                text="Sepete Ekle",
                height=36,
                corner_radius=T.RADIUS_SM,
                fg_color=T.PRIMARY,
                hover_color=T.PRIMARY_HOVER,
                font=T.font_body(12),
                command=lambda p=product: self._add_to_cart(p),
            ).pack(padx=12, pady=(0, 12), fill="x")

    def _load_product_image(self, product: dict, label: ctk.CTkLabel):
        path = product.get("image_path")
        if not path:
            label.configure(text="Görsel yok", text_color=T.TEXT_MUTED, font=T.font_small(11))
            return

        url = f"{self.app.config_data['server_url'].rstrip('/')}{path}"

        def worker():
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    data = response.read()
                image = Image.open(io.BytesIO(data))
                image = image.resize((140, 140))
                photo = ctk.CTkImage(light_image=image, dark_image=image, size=(140, 140))
                self.after(0, lambda: self._apply_product_image(product["id"], label, photo))
            except Exception:
                self.after(0, lambda: label.configure(text="Yüklenemedi", text_color=T.TEXT_MUTED))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_product_image(self, product_id: int, label: ctk.CTkLabel, photo: ctk.CTkImage):
        self._product_images[product_id] = photo
        label.configure(image=photo, text="")

    def _add_to_cart(self, product: dict):
        pid = product["id"]
        current = self.cart.get(pid, {"product": product, "quantity": 0})
        if current["quantity"] >= product["stock"]:
            self.app.show_error("Stok yetersiz.")
            return
        current["quantity"] += 1
        self.cart[pid] = current
        self._render_cart()

    def _render_cart(self):
        for widget in self.cart_list.winfo_children():
            widget.destroy()

        total = 0.0
        count = 0
        for item in self.cart.values():
            product = item["product"]
            qty = item["quantity"]
            line = product["price"] * qty
            total += line
            count += qty

            row = ctk.CTkFrame(self.cart_list, fg_color=T.SURFACE, corner_radius=T.RADIUS_SM)
            row.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                inner,
                text=f"{product['name']}",
                font=T.font_body(12),
                text_color=T.TEXT,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                inner,
                text=f"x{qty}",
                font=T.font_small(11),
                text_color=T.TEXT_MUTED,
            ).pack(side="left", padx=(4, 8))

            ctk.CTkLabel(
                inner,
                text=f"{line:.2f} ₺",
                font=T.font_body(12),
                text_color=T.TEXT,
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                inner,
                text="−",
                width=28,
                height=28,
                corner_radius=6,
                fg_color=T.SURFACE_ALT,
                hover_color=T.BORDER,
                text_color=T.TEXT,
                command=lambda p=product["id"]: self._decrease_item(p),
            ).pack(side="right")

        self.total_label.configure(text=f"Toplam: {total:.2f} ₺")
        self.cart_count.configure(text=f"{count} ürün")
        self._update_checkout_popup_total()

    def _decrease_item(self, product_id: int):
        if product_id not in self.cart:
            return
        self.cart[product_id]["quantity"] -= 1
        if self.cart[product_id]["quantity"] <= 0:
            del self.cart[product_id]
        self._render_cart()

    def _open_add_product(self):
        AddProductDialog(self, self.app, on_success=self._load_products)

    def _start_checkout(self):
        if not self.cart:
            self.app.show_error("Sepet boş.")
            return
        self._awaiting_payment = True
        self._show_checkout_popup()

    def _handle_rfid(self, uid: str):
        if not self._awaiting_payment:
            return

        items = [
            {"product_id": pid, "quantity": data["quantity"]}
            for pid, data in self.cart.items()
        ]
        self.checkout_message.configure(text="Ödeme işleniyor, lütfen bekleyin...", text_color=T.TEXT_MUTED)

        def work():
            return self.app.api.purchase(uid, items)

        def on_success(result):
            self._awaiting_payment = False
            self._hide_checkout_popup()
            self.app.show_info(
                f"{result['message']}\nKalan bakiye: {result['remaining_balance']:.2f} ₺"
            )
            self.cart.clear()
            self._render_cart()
            self._load_products()
            self.after(1500, lambda: self.app.show_page("home"))

        def on_error(exc):
            self.app.show_error(str(exc))
            self.checkout_message.configure(
                text="Kartınızı RFID okuyucuya okutunuz.",
                text_color=T.TEXT,
            )

        self.app.run_in_background(work, on_success=on_success, on_error=on_error)

    def grid_forget(self):
        self.on_hide()
        super().grid_forget()
