import customtkinter as ctk

from client import theme as T


class RegisterDialog(ctk.CTkToplevel):
    def __init__(self, parent, app, card_uid: str, on_success=None):
        super().__init__(parent)
        self.app = app
        self.card_uid = card_uid
        self.on_success = on_success

        self.title("Yeni Kart Kaydı")
        self.geometry("500x460")
        self.resizable(False, False)
        self.configure(fg_color=T.CONTENT_BG)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        shell = T.card(self)
        shell.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            shell,
            text="Müşteri Kaydı",
            font=T.font_title(22),
            text_color=T.TEXT,
        ).pack(padx=T.PAD_CARD, pady=(T.PAD_CARD, 4), anchor="w")

        uid_box = ctk.CTkFrame(shell, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM)
        uid_box.pack(fill="x", padx=T.PAD_CARD, pady=(8, 16))

        ctk.CTkLabel(
            uid_box,
            text=f"Kart UID: {card_uid}",
            font=T.font_body(13),
            text_color=T.TEXT_MUTED,
        ).pack(padx=14, pady=10, anchor="w")

        form = ctk.CTkFrame(shell, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=T.PAD_CARD)

        self.first_name = self._field(form, "Ad", 0)
        self.last_name = self._field(form, "Soyad", 1)
        self.email = self._field(form, "E-posta", 2)
        self.phone = self._field(form, "Telefon", 3)

        btn_row = ctk.CTkFrame(shell, fg_color="transparent")
        btn_row.pack(fill="x", padx=T.PAD_CARD, pady=(8, T.PAD_CARD))

        T.ghost_btn(btn_row, text="İptal", width=100, command=self.destroy).pack(side="right", padx=(8, 0))
        T.primary_btn(btn_row, text="Kaydet", width=120, command=self._save).pack(side="right")

    def _field(self, parent, label: str, row: int):
        ctk.CTkLabel(
            parent,
            text=label,
            font=T.font_body(13),
            text_color=T.TEXT_MUTED,
        ).grid(row=row, column=0, sticky="w", pady=10)
        entry = T.entry(parent, width=320)
        entry.grid(row=row, column=1, sticky="ew", pady=10, padx=(12, 0))
        parent.grid_columnconfigure(1, weight=1)
        return entry

    def _save(self):
        from client.services.api_client import ApiError

        data = {
            "card_uid": self.card_uid,
            "first_name": self.first_name.get().strip(),
            "last_name": self.last_name.get().strip(),
            "email": self.email.get().strip(),
            "phone": self.phone.get().strip(),
        }

        if not all(data.values()):
            self.app.show_error("Tüm alanları doldurun.")
            return

        try:
            card = self.app.api.register_card(data)
        except ApiError as exc:
            self.app.show_error(str(exc))
            return

        if self.on_success:
            self.on_success(card)
        self.destroy()
