"""Small HTML building blocks. HTML strings are single-line with no leading spaces so that
Streamlit's Markdown renderer does not turn them into code blocks. Dynamic text is escaped."""
from __future__ import annotations

import base64
import functools
import html
from pathlib import Path

import streamlit as st

import config


def esc(x) -> str:
    return html.escape(str(x))


@functools.lru_cache(maxsize=32)
def image_b64(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    return base64.b64encode(p.read_bytes()).decode("ascii")


def banner_b64() -> str | None:
    for p in config.BANNER_CANDIDATES:
        b = image_b64(str(p))
        if b:
            return b
    return None


def crop_image_tag(stem: str, size: int = 78) -> str:
    for ext, mime in (("png", "png"), ("jpg", "jpeg"), ("jpeg", "jpeg"), ("webp", "webp")):
        p = config.CROP_IMG_DIR / f"{stem}.{ext}"
        b = image_b64(str(p))
        if b:
            return f'<img src="data:image/{mime};base64,{b}" alt="{esc(stem)}" style="width:{size}px;height:{size}px;object-fit:contain">'
    return '<div style="font-size:2.4rem">🌱</div>'


def page_header(icon: str, title: str, subtitle: str) -> None:
    st.markdown(f'<div class="cy-head"><div class="ico">{icon}</div><div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div></div>',
                unsafe_allow_html=True)


def stat_card(icon: str, value, label: str, sub: str = "") -> str:
    return (f'<div class="cy-stat"><div class="ico">{icon}</div><div class="val">{esc(value)}</div>'
            f'<div class="lab">{esc(label)}</div><div class="sub">{esc(sub)}</div></div>')


def metric_card(label: str, value: str, unit: str = "", sub: str = "") -> str:
    return (f'<div class="cy-metric"><div class="lab">{esc(label)}</div><div class="val">{esc(value)}</div>'
            f'<div class="unit">{esc(unit)}</div><div class="sub">{esc(sub)}</div></div>')


def kv_table(rows: list[tuple[str, str]]) -> str:
    body = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in rows)
    return f'<table class="cy-table">{body}</table>'


def check_list(items: list[str], cls: str = "cy-list") -> str:
    return f'<ul class="{cls}">' + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


def tagged_list(items: list[tuple[str, str]]) -> str:
    out = []
    for tag, text in items:
        label = "FROM YOUR DATA" if tag == "data" else "GENERAL GUIDANCE"
        out.append(f'<li><span class="tag {esc(tag)}">{label}</span>{esc(text)}</li>')
    return '<ul class="cy-list">' + "".join(out) + "</ul>"


def warning_box(text: str) -> str:
    return f'<div class="cy-warn">⚠️ {esc(text)}</div>'


DISCLAIMER = ("Predictions are statistical estimates from historical records, not guaranteed harvest outcomes. "
              "Real yields depend on soil, weather, seed variety, pests and management that this model does not see.")
