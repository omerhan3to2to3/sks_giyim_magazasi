import threading

import customtkinter as ctk
from tkinter import messagebox

from .config import load_config, normalize_server_url, save_config
from .services.api_client import ApiClient
from .services.rfid_reader import RfidReader
from .pages.home import HomePage
from .pages.shopping import ShoppingPage
from .pages.statistics import StatisticsPage
from .pages.topup import TopUpPage
from . import theme as T


class GiyimMagazasiApp(ctk.CTk):
    NAV_ITEMS = [
        ("home", "Ana Sayfa"),
        ("topup", "Para Yükleme"),
        ("shopping", "Alışveriş"),
        ("statistics", "İstatistikler"),
    ]

    def __init__(self):
        super().__init__()

        self.config_data = load_config()
        self.api = ApiClient(self.config_data["server_url"])
        self.rfid = RfidReader(self._on_rfid_read, self.config_data.get("serial_port"))

        self.title("Giyim Mağazası — Satış Sistemi")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(fg_color=T.CONTENT_BG)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self._rfid_callbacks = []
        self._current_page = None
        self._pages = {}

        self._build_layout()
        self.show_page("home")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self,
            width=248,
            corner_radius=0,
            fg_color=T.SIDEBAR_BG,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)
        self.sidebar.grid_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(28, 20))

        ctk.CTkLabel(
            brand_frame,
            text="GIYIM",
            font=T.font_brand(22),
            text_color=T.TEXT_ON_DARK,
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_frame,
            text="MAĞAZASI",
            font=T.font_brand(22),
            text_color=T.PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand_frame,
            text="Satış & Bakiye Sistemi",
            font=T.font_small(12),
            text_color=T.TEXT_MUTED_DARK,
        ).pack(anchor="w", pady=(10, 0))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=T.SIDEBAR_BORDER).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 12)
        )

        ctk.CTkLabel(
            self.sidebar,
            text="MENÜ",
            font=T.font_small(10),
            text_color=T.TEXT_MUTED_DARK,
        ).grid(row=2, column=0, padx=24, pady=(0, 8), sticky="w")

        self.nav_buttons = {}
        for idx, (key, label) in enumerate(self.NAV_ITEMS, start=3):
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {label}",
                anchor="w",
                height=44,
                corner_radius=T.RADIUS_SM,
                fg_color=T.NAV_IDLE,
                hover_color=T.NAV_IDLE_HOVER,
                text_color=T.TEXT_ON_DARK,
                font=T.font_body(13),
                command=lambda k=key: self.show_page(k),
            )
            btn.grid(row=idx, column=0, padx=16, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        status_panel = ctk.CTkFrame(
            self.sidebar,
            fg_color=T.NAV_IDLE,
            corner_radius=T.RADIUS_MD,
            border_width=1,
            border_color=T.SIDEBAR_BORDER,
        )
        status_panel.grid(row=8, column=0, padx=16, pady=(0, 20), sticky="ew")

        ctk.CTkLabel(
            status_panel,
            text="Sistem Durumu",
            font=T.font_section(12),
            text_color=T.TEXT_MUTED_DARK,
        ).pack(anchor="w", padx=14, pady=(12, 8))

        self.connection_label = ctk.CTkLabel(
            status_panel,
            text="Sunucu: kontrol ediliyor...",
            font=T.font_small(11),
            text_color=T.TEXT_MUTED_DARK,
            wraplength=200,
            justify="left",
        )
        self.connection_label.pack(anchor="w", padx=14, pady=(0, 6))

        self.rfid_label = ctk.CTkLabel(
            status_panel,
            text="RFID: bağlanıyor...",
            font=T.font_small(11),
            text_color=T.TEXT_MUTED_DARK,
            wraplength=200,
            justify="left",
        )
        self.rfid_label.pack(anchor="w", padx=14, pady=(0, 6))

        self.last_card_label = ctk.CTkLabel(
            status_panel,
            text="Son kart: —",
            font=T.font_small(11),
            text_color=T.TEXT_MUTED_DARK,
            wraplength=200,
            justify="left",
        )
        self.last_card_label.pack(anchor="w", padx=14, pady=(0, 14))

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=T.CONTENT_BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._pages["home"] = HomePage(self.content, self)
        self._pages["topup"] = TopUpPage(self.content, self)
        self._pages["shopping"] = ShoppingPage(self.content, self)
        self._pages["statistics"] = StatisticsPage(self.content, self)

        self._connection_check_running = False
        self.after(500, self._check_connections)
        self.rfid.on_status = self._on_rfid_status
        self.rfid.start_listening()
        self._update_rfid_status()

    def show_page(self, name: str):
        if self._current_page:
            self._pages[self._current_page].grid_forget()

        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color=T.NAV_ACTIVE, hover_color=T.PRIMARY_HOVER)
            else:
                btn.configure(fg_color=T.NAV_IDLE, hover_color=T.NAV_IDLE_HOVER)

        self._current_page = name
        page = self._pages[name]
        page.grid(row=0, column=0, sticky="nsew")
        page.on_show()

    def register_rfid_callback(self, callback):
        self._rfid_callbacks.append(callback)

    def unregister_rfid_callback(self, callback):
        if callback in self._rfid_callbacks:
            self._rfid_callbacks.remove(callback)

    def _on_rfid_read(self, uid: str):
        self.after(0, lambda: self._dispatch_rfid(uid))

    def _dispatch_rfid(self, uid: str):
        self.last_card_label.configure(text=f"Son kart: {uid}", text_color=T.STATUS_OK)
        if not self._rfid_callbacks:
            if self._current_page == "home":
                self.last_card_label.configure(
                    text=f"Kart okundu: {uid}\nPara Yükleme veya Alışveriş sayfasına gidin",
                    text_color=T.STATUS_WARN,
                )
            return
        for callback in list(self._rfid_callbacks):
            callback(uid)

    def _on_rfid_status(self, status: str):
        self.after(0, lambda: self._apply_rfid_status(status))

    def _apply_rfid_status(self, status: str):
        port = self.config_data.get("serial_port", "COM3")
        if status == "ready":
            self.rfid_label.configure(
                text=f"RFID: {port}\nModül hazır",
                text_color=T.STATUS_OK,
            )
        elif status == "module_error":
            self.rfid_label.configure(
                text=f"RFID: {port}\nModül bulunamadı!\nKablo ve kütüphane kontrol",
                text_color=T.STATUS_ERR,
            )

    def _check_connections(self):
        if self._connection_check_running:
            self.after(5000, self._check_connections)
            return

        self._connection_check_running = True

        def worker():
            ok = self.api.health()
            self.after(0, lambda: self._apply_connection_status(ok))

        threading.Thread(target=worker, daemon=True).start()
        self.after(5000, self._check_connections)

    def _apply_connection_status(self, ok: bool):
        self._connection_check_running = False
        if ok:
            self.connection_label.configure(
                text=f"Sunucu: bağlı\n{self.config_data['server_url']}",
                text_color=T.STATUS_OK,
            )
        else:
            self.connection_label.configure(
                text=f"Sunucu: bağlantı yok\n{self.config_data['server_url']}",
                text_color=T.STATUS_ERR,
            )

    def _update_rfid_status(self):
        ports = RfidReader.list_ports()
        port = self.config_data.get("serial_port", "COM3")

        if self.rfid.last_error and "Eri" in self.rfid.last_error:
            self.rfid_label.configure(
                text=f"RFID: {port}\nPort başka programda açık!\nSerial Monitor'u kapatın",
                text_color=T.STATUS_ERR,
            )
            self.after(5000, self._update_rfid_status)
            return

        if self.rfid.is_connected and self.rfid.module_ready:
            self.rfid_label.configure(text=f"RFID: {port}\nModül hazır", text_color=T.STATUS_OK)
        elif self.rfid.is_connected:
            self.rfid_label.configure(
                text=f"RFID: {port}\nBağlı, modül bekleniyor...\nAyarlar > Yeniden Bağlan",
                text_color=T.STATUS_WARN,
            )
        elif port in ports:
            self.rfid_label.configure(
                text=f"RFID: {port}\nPorta bağlanılamadı",
                text_color=T.STATUS_ERR,
            )
        else:
            self.rfid_label.configure(
                text=f"RFID: port bulunamadı\n({port})",
                text_color=T.STATUS_ERR,
            )
        self.after(5000, self._update_rfid_status)

    def show_error(self, message: str):
        messagebox.showerror("Hata", message)

    def show_info(self, message: str):
        messagebox.showinfo("Bilgi", message)

    def update_server_url(self, url: str):
        url = normalize_server_url(url)
        self.config_data["server_url"] = url
        save_config(self.config_data)
        self.api = ApiClient(url)

    def run_in_background(self, work, on_success=None, on_error=None):
        def worker():
            try:
                result = work()
            except Exception as exc:
                if on_error:
                    self.after(0, lambda: on_error(exc))
                return
            if on_success:
                self.after(0, lambda: on_success(result))

        threading.Thread(target=worker, daemon=True).start()

    def update_serial_port(self, port: str):
        self.config_data["serial_port"] = port
        save_config(self.config_data)
        self.rfid.disconnect()
        self.rfid.port = port
        self.rfid.start_listening()
        self._update_rfid_status()

    def _on_close(self):
        self.rfid.disconnect()
        self.destroy()

