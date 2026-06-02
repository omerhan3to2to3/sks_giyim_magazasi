"""Ortak UI renkleri, fontlar ve yardımcı bileşenler."""

import customtkinter as ctk


# Palet — butik / mağaza hissi
SIDEBAR_BG = "#1a2332"
SIDEBAR_BORDER = "#2a3548"
CONTENT_BG = "#eef1f6"
SURFACE = "#ffffff"
SURFACE_ALT = "#f8fafc"
BORDER = "#dde3ec"

PRIMARY = "#2563eb"
PRIMARY_HOVER = "#1d4ed8"
SUCCESS = "#059669"
SUCCESS_HOVER = "#047857"
WARNING = "#d97706"
DANGER = "#dc2626"
PURPLE = "#7c3aed"
PURPLE_HOVER = "#6d28d9"
SKY = "#0ea5e9"
SKY_HOVER = "#0284c7"

TEXT = "#0f172a"
TEXT_MUTED = "#64748b"
TEXT_ON_DARK = "#e2e8f0"
TEXT_MUTED_DARK = "#94a3b8"

NAV_ACTIVE = PRIMARY
NAV_IDLE = "#243044"
NAV_IDLE_HOVER = "#2f3d52"

STATUS_OK = SUCCESS
STATUS_WARN = WARNING
STATUS_ERR = DANGER

RADIUS_LG = 16
RADIUS_MD = 12
RADIUS_SM = 8

PAD_PAGE = 36
PAD_CARD = 24


def font_brand(size=20):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")


def font_title(size=30):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")


def font_subtitle(size=14):
    return ctk.CTkFont(family="Segoe UI", size=size)


def font_section(size=18):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")


def font_body(size=13):
    return ctk.CTkFont(family="Segoe UI", size=size)


def font_small(size=11):
    return ctk.CTkFont(family="Segoe UI", size=size)


def font_stat(size=26):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")


def card(parent, **kwargs):
    opts = dict(
        fg_color=SURFACE,
        corner_radius=RADIUS_LG,
        border_width=1,
        border_color=BORDER,
    )
    opts.update(kwargs)
    return ctk.CTkFrame(parent, **opts)


def primary_btn(parent, **kwargs):
    opts = dict(
        fg_color=PRIMARY,
        hover_color=PRIMARY_HOVER,
        corner_radius=RADIUS_SM,
        height=38,
        font=font_body(13),
    )
    opts.update(kwargs)
    return ctk.CTkButton(parent, **opts)


def ghost_btn(parent, **kwargs):
    opts = dict(
        fg_color="transparent",
        hover_color=SURFACE_ALT,
        border_width=1,
        border_color=BORDER,
        text_color=TEXT,
        corner_radius=RADIUS_SM,
        height=38,
        font=font_body(13),
    )
    opts.update(kwargs)
    return ctk.CTkButton(parent, **opts)


def entry(parent, **kwargs):
    opts = dict(
        height=40,
        corner_radius=RADIUS_SM,
        border_color=BORDER,
        font=font_body(13),
    )
    opts.update(kwargs)
    return ctk.CTkEntry(parent, **opts)


def build_page_header(parent, title: str, subtitle: str = ""):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.grid_columnconfigure(1, weight=1)

    accent = ctk.CTkFrame(header, width=4, height=48, fg_color=PRIMARY, corner_radius=2)
    accent.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 16))
    accent.grid_propagate(False)

    title_lbl = ctk.CTkLabel(header, text=title, font=font_title(), text_color=TEXT)
    title_lbl.grid(row=0, column=1, sticky="w")

    if subtitle:
        sub_lbl = ctk.CTkLabel(
            header,
            text=subtitle,
            font=font_subtitle(),
            text_color=TEXT_MUTED,
        )
        sub_lbl.grid(row=1, column=1, sticky="w", pady=(6, 0))

    return header
