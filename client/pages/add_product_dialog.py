from tkinter import filedialog

import customtkinter as ctk

from client import theme as T
from client.services.api_client import ApiError


class AddProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, on_success=None):
        super().__init__(parent)
        self.app = app
        self.on_success = on_success
        self.image_path = None

        self.title("Ürün Ekle")
        self.geometry("540x520")
        self.resizable(False, False)
        self.configure(fg_color=T.CONTENT_BG)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        shell = T.card(self)
        shell.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            shell,
            text="Yeni Ürün",
            font=T.font_title(22),
            text_color=T.TEXT,
        ).pack(padx=T.PAD_CARD, pady=(T.PAD_CARD, 16), anchor="w")

        form = ctk.CTkFrame(shell, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=T.PAD_CARD)

        self.product_code = self._field(form, "Ürün ID", 0)
        self.name = self._field(form, "Ürün Adı", 1)
        self.price = self._field(form, "Fiyat (₺)", 2)
        self.stock = self._field(form, "Stok Adedi", 3)

        img_row = ctk.CTkFrame(form, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM)
        img_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=14)

        inner = ctk.CTkFrame(img_row, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(inner, text="Fotoğraf", font=T.font_body(13), text_color=T.TEXT_MUTED).pack(
            side="left"
        )
        self.image_label = ctk.CTkLabel(
            inner,
            text="Seçilmedi",
            font=T.font_small(12),
            text_color=T.TEXT_MUTED,
        )
        self.image_label.pack(side="left", padx=12)
        T.ghost_btn(inner, text="Dosya Seç", width=100, command=self._pick_image).pack(side="right")

        btn_row = ctk.CTkFrame(shell, fg_color="transparent")
        btn_row.pack(fill="x", padx=T.PAD_CARD, pady=(8, T.PAD_CARD))

        T.ghost_btn(btn_row, text="İptal", width=100, command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            btn_row,
            text="Kaydet",
            width=120,
            height=38,
            corner_radius=T.RADIUS_SM,
            fg_color=T.SUCCESS,
            hover_color=T.SUCCESS_HOVER,
            font=T.font_body(13),
            command=self._save,
        ).pack(side="right")

    def _field(self, parent, label: str, row: int):
        ctk.CTkLabel(
            parent,
            text=label,
            font=T.font_body(13),
            text_color=T.TEXT_MUTED,
        ).grid(row=row, column=0, sticky="w", pady=10)
        entry = T.entry(parent, width=340)
        entry.grid(row=row, column=1, sticky="ew", pady=10, padx=(12, 0))
        parent.grid_columnconfigure(1, weight=1)
        return entry

    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Ürün fotoğrafı seç",
            filetypes=[("Görseller", "*.jpg *.jpeg *.png *.webp"), ("Tüm dosyalar", "*.*")],
        )
        if path:
            self.image_path = path
            self.image_label.configure(
                text=path.split("/")[-1].split("\\")[-1],
                text_color=T.TEXT,
            )

    def _save(self):
        code = self.product_code.get().strip()
        name = self.name.get().strip()
        price_text = self.price.get().strip().replace(",", ".")
        stock_text = self.stock.get().strip() or "0"

        if not code or not name or not price_text:
            self.app.show_error("Ürün ID, ad ve fiyat zorunludur.")
            return

        try:
            price = float(price_text)
            stock = int(stock_text)
            if price <= 0 or stock < 0:
                raise ValueError
        except ValueError:
            self.app.show_error("Geçerli fiyat ve stok girin.")
            return

        try:
            if self.image_path:
                self.app.api.create_product_with_image(
                    {
                        "product_code": code,
                        "name": name,
                        "price": str(price),
                        "stock": str(stock),
                    },
                    self.image_path,
                )
            else:
                self.app.api.create_product(
                    {
                        "product_code": code,
                        "name": name,
                        "price": price,
                        "stock": stock,
                    }
                )
        except ApiError as exc:
            self.app.show_error(str(exc))
            return

        if self.on_success:
            self.on_success()
        self.app.show_info("Ürün eklendi.")
        self.destroy()
