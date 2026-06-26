import customtkinter as ctk

from client import theme as T


class HomePage(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = T.build_page_header(
            self,
            "Hoş Geldiniz",
            "Sol menüden işlem seçin veya aşağıdaki kısayolları kullanın.",
        )
        header.grid(row=0, column=0, sticky="ew", padx=T.PAD_PAGE, pady=(T.PAD_PAGE, 12))

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", padx=T.PAD_PAGE, pady=12)
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1)

        shortcuts = [
            ("Para Yükleme", "Kart kaydı ve bakiye yükleme işlemleri", "topup", T.SKY, T.SKY_HOVER),
            ("Alışveriş", "Ürün satışı ve sepet yönetimi", "shopping", T.SUCCESS, T.SUCCESS_HOVER),
            ("İstatistikler", "Satış ve ürün raporları", "statistics", T.PURPLE, T.PURPLE_HOVER),
        ]

        for col, (title, desc, page, color, hover) in enumerate(shortcuts):
            card = T.card(cards)
            card.grid(row=0, column=col, padx=8, pady=8, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            stripe = ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=0)
            stripe.grid(row=0, column=0, sticky="ew")

            ctk.CTkLabel(
                card,
                text=title,
                font=T.font_section(20),
                text_color=T.TEXT,
            ).grid(row=1, column=0, padx=T.PAD_CARD, pady=(20, 8), sticky="w")

            ctk.CTkLabel(
                card,
                text=desc,
                font=T.font_body(13),
                text_color=T.TEXT_MUTED,
                wraplength=260,
                justify="left",
            ).grid(row=2, column=0, padx=T.PAD_CARD, pady=(0, 20), sticky="w")

            ctk.CTkButton(
                card,
                text="Sayfaya Git →",
                fg_color=color,
                hover_color=hover,
                corner_radius=T.RADIUS_SM,
                height=40,
                font=T.font_body(13),
                command=lambda p=page: self.app.show_page(p),
            ).grid(row=3, column=0, padx=T.PAD_CARD, pady=(0, T.PAD_CARD), sticky="ew")

        settings = T.card(self)
        settings.grid(row=2, column=0, sticky="nsew", padx=T.PAD_PAGE, pady=(12, T.PAD_PAGE))
        settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            settings,
            text="Bağlantı Ayarları",
            font=T.font_section(),
            text_color=T.TEXT,
        ).grid(row=0, column=0, columnspan=2, padx=T.PAD_CARD, pady=(T.PAD_CARD, 16), sticky="w")

        ctk.CTkLabel(
            settings,
            text="Sunucu Adresi",
            font=T.font_body(13),
            text_color=T.TEXT_MUTED,
        ).grid(row=1, column=0, padx=T.PAD_CARD, pady=8, sticky="w")
        self.server_entry = T.entry(settings, width=400, placeholder_text="http://192.168.1.10:8000")
        self.server_entry.grid(row=1, column=1, padx=T.PAD_CARD, pady=8, sticky="ew")
        self.server_entry.insert(0, self.app.config_data["server_url"])

        ctk.CTkLabel(
            settings,
            text="RFID Port",
            font=T.font_body(13),
            text_color=T.TEXT_MUTED,
        ).grid(row=2, column=0, padx=T.PAD_CARD, pady=8, sticky="w")
        self.port_entry = T.entry(settings, width=200, placeholder_text="COM3")
        self.port_entry.grid(row=2, column=1, padx=T.PAD_CARD, pady=8, sticky="w")
        self.port_entry.insert(0, self.app.config_data.get("serial_port", "COM3"))

        btn_row = ctk.CTkFrame(settings, fg_color="transparent")
        btn_row.grid(row=3, column=1, padx=T.PAD_CARD, pady=(12, 8), sticky="w")

        T.primary_btn(btn_row, text="Ayarları Kaydet", command=self._save_settings).pack(
            side="left", padx=(0, 10)
        )
        T.ghost_btn(btn_row, text="RFID Yeniden Bağlan", command=self._reconnect_rfid).pack(side="left")

        info = ctk.CTkFrame(settings, fg_color=T.SURFACE_ALT, corner_radius=T.RADIUS_SM)
        info.grid(row=4, column=0, columnspan=2, padx=T.PAD_CARD, pady=(8, T.PAD_CARD), sticky="ew")

        ctk.CTkLabel(
            info,
            text="Sunucu COM portunu kullanmaz. RFID yalnızca bu bilgisayardaki okuyucu üzerinden çalışır.\n"
            "İki bilgisayar kullanıyorsanız sunucu adresini para yükleme PC'sinin IP'sine ayarlayın.",
            font=T.font_small(12),
            text_color=T.TEXT_MUTED,
            justify="left",
        ).pack(padx=16, pady=14, anchor="w")

    def on_show(self):
        pass
    def _reconnect_rfid(self):
        port = self.port_entry.get().strip()
        if port:
            self.app.update_serial_port(port)
        else:
            self.app.rfid.disconnect()
            self.app.rfid.start_listening()
            self.app._update_rfid_status()
        self.app.show_info("RFID bağlantısı yenilendi.")

    def _save_settings(self):
        url = self.server_entry.get().strip()
        port = self.port_entry.get().strip()
        if url:
            self.app.update_server_url(url)
            self.server_entry.delete(0, "end")
            self.server_entry.insert(0, self.app.config_data["server_url"])
        if port:
            self.app.update_serial_port(port)
        self.app.show_info("Ayarlar kaydedildi.")


