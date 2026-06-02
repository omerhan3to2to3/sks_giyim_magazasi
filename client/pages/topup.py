import customtkinter as ctk

from client import theme as T
from .register_dialog import RegisterDialog


class TopUpPage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._rfid_callback = None
        self._topup_amount = None

        self.grid_columnconfigure(0, weight=1)

        header = T.build_page_header(
            self,
            "Para Yükleme",
            "Yüklenecek tutarı girin ve kartı okuyucuya yaklaştırın.",
        )
        header.grid(row=0, column=0, sticky="ew", padx=T.PAD_PAGE, pady=(T.PAD_PAGE, 12))

        panel = T.card(self)
        panel.grid(row=1, column=0, sticky="ew", padx=T.PAD_PAGE, pady=12)
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text="Yüklenecek Tutar",
            font=T.font_section(),
            text_color=T.TEXT,
        ).grid(row=0, column=0, padx=T.PAD_CARD, pady=(T.PAD_CARD, 12), sticky="w")

        amount_row = ctk.CTkFrame(panel, fg_color="transparent")
        amount_row.grid(row=1, column=0, padx=T.PAD_CARD, pady=8, sticky="ew")

        self.amount_entry = T.entry(amount_row, width=180, placeholder_text="Örn: 100")
        self.amount_entry.pack(side="left", padx=(0, 16))

        for value in [50, 100, 200, 500]:
            ctk.CTkButton(
                amount_row,
                text=f"{value} ₺",
                width=72,
                height=40,
                corner_radius=T.RADIUS_SM,
                fg_color=T.SURFACE_ALT,
                hover_color=T.BORDER,
                text_color=T.TEXT,
                border_width=1,
                border_color=T.BORDER,
                font=T.font_body(13),
                command=lambda v=value: self._set_amount(v),
            ).pack(side="left", padx=4)

        status_box = ctk.CTkFrame(panel, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM)
        status_box.grid(row=2, column=0, padx=T.PAD_CARD, pady=(20, 8), sticky="ew")

        self.status_label = ctk.CTkLabel(
            status_box,
            text="Tutarı girdikten sonra kartı RFID okuyucuya yaklaştırın.",
            font=T.font_body(14),
            text_color=T.TEXT,
            wraplength=600,
            justify="left",
        )
        self.status_label.pack(padx=16, pady=14, anchor="w")

        self.card_info = ctk.CTkLabel(panel, text="", font=T.font_body(13), text_color=T.SUCCESS)
        self.card_info.grid(row=3, column=0, padx=T.PAD_CARD, pady=(0, T.PAD_CARD), sticky="w")

        test_row = T.card(self)
        test_row.grid(row=2, column=0, padx=T.PAD_PAGE, pady=(0, T.PAD_PAGE), sticky="ew")

        inner = ctk.CTkFrame(test_row, fg_color="transparent")
        inner.pack(fill="x", padx=T.PAD_CARD, pady=16)

        ctk.CTkLabel(
            inner,
            text="Test modu",
            font=T.font_section(14),
            text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(0, 16))
        self.test_entry = T.entry(inner, width=140, placeholder_text="Kart UID")
        self.test_entry.pack(side="left", padx=(0, 10))
        T.ghost_btn(inner, text="Simüle Et", width=100, command=self._simulate).pack(side="left")

    def on_show(self):
        self.amount_entry.delete(0, "end")
        self.status_label.configure(text="Tutarı girdikten sonra kartı RFID okuyucuya yaklaştırın.")
        self.card_info.configure(text="")
        self._rfid_callback = self._handle_rfid
        self.app.register_rfid_callback(self._rfid_callback)

    def on_hide(self):
        if self._rfid_callback:
            self.app.unregister_rfid_callback(self._rfid_callback)

    def _set_amount(self, value: int):
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, str(value))

    def _get_amount(self):
        amount_text = self.amount_entry.get().strip().replace(",", ".")
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
            return amount
        except ValueError:
            return None

    def _simulate(self):
        uid = self.test_entry.get().strip()
        if uid:
            self._handle_rfid(uid.upper())

    def _handle_rfid(self, uid: str):
        amount = self._get_amount()
        if amount is None:
            self.app.show_error("Önce geçerli bir tutar girin.")
            return

        self.status_label.configure(text="Kart kontrol ediliyor...")

        def work():
            return self.app.api.lookup_card(uid)

        def on_success(result):
            if not result["exists"]:
                self.status_label.configure(text=f"Yeni kart: {uid} — Kayıt gerekli")
                RegisterDialog(
                    self,
                    self.app,
                    uid,
                    on_success=self._after_register,
                )
                return
            self._do_topup(uid, amount)

        def on_error(exc):
            self.status_label.configure(text="Tutarı girdikten sonra kartı RFID okuyucuya yaklaştırın.")
            self.app.show_error(str(exc))

        self.app.run_in_background(work, on_success=on_success, on_error=on_error)

    def _after_register(self, card: dict):
        self.app.show_info(
            f"{card['first_name']} {card['last_name']} kaydedildi.\n"
            "Bakiye 0 TL olarak atandı. Para yüklemek için tekrar bu sayfaya gelin."
        )
        self.after(1500, lambda: self.app.show_page("home"))

    def _do_topup(self, uid: str, amount: float):
        self.status_label.configure(text="Para yükleniyor...")

        def work():
            return self.app.api.topup_card(uid, amount)

        def on_success(result):
            card = result["card"]
            self.status_label.configure(text="Para yükleme başarılı!")
            self.card_info.configure(
                text=f"{card['first_name']} {card['last_name']}  ·  Yeni bakiye: {card['balance']:.2f} ₺"
            )
            self.app.show_info(result["message"])
            self.after(2000, lambda: self.app.show_page("home"))

        def on_error(exc):
            self.status_label.configure(text="Tutarı girdikten sonra kartı RFID okuyucuya yaklaştırın.")
            self.app.show_error(str(exc))

        self.app.run_in_background(work, on_success=on_success, on_error=on_error)

    def grid_forget(self):
        self.on_hide()
        super().grid_forget()
