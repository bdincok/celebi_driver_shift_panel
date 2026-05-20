# -*- coding: utf-8 -*-
"""
Çelebi Hava Hizmetleri - Sürücü Vardiya ve Araç Yönetim Paneli
Streamlit + SQLite tek dosya uygulama.

Çalıştırma:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import base64
import os
import sqlite3
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except Exception:  # Plotly yüklenmezse uygulama çalışmaya devam eder.
    px = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:
    colors = None
    SimpleDocTemplate = None


APP_TITLE = "Çelebi Sürücü Vardiya ve Araç Yönetim Paneli"
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "data"
DB_PATH = DB_DIR / "celebi_driver_panel.sqlite3"
LOGO_PATH = BASE_DIR / "assets" / "celebi_logo.png"

INITIAL_GROUPS = [
    ("Genel Sürücüler", "Başlangıçta tüm sürücülerin bağlı olduğu genel grup."),
    ("VIP Sürücüleri", "VIP yolcu, karşılama ve özel görev operasyonları."),
    ("Şut Altı / Bagaj Sürücüleri", "Bagaj, şut altı ve operasyon destek araçları."),
    ("Apron Sürücüleri", "Apron sahası rutin araç operasyonları."),
    ("Ağır Vasıta", "Otobüs, çekici, high-loader ve ağır araç kullanan ekip."),
    ("Terminal Operasyon", "Terminal içi/yakın çevre sürüş ve destek görevleri."),
    ("Uçak Altı Operasyon", "Uçak altı ve turnaround destek görevleri."),
    ("Transfer Sürücüleri", "Personel, ekipman veya yolcu transfer görevleri."),
    ("Gece Operasyon", "Gece vardiyası ve düşük yoğunluk operasyon ekibi."),
    ("Yedek / Takviye Ekip", "Operasyon yoğunluğuna göre destek veren ekip."),
]

INITIAL_DRIVERS = [
    "UMUT BOĞA",
    "MAZ_LUM İBRAHİM AKYOL",
    "MAHMUT KARADOĞAN",
    "ÖMER ELE",
    "TAYFUN ÜZÜM",
    "MUHAMMET EFE BECİT",
    "KENAN KANDO",
    "İSA CEYLAN",
    "DOĞAN KIŞLA",
    "HEYBET KÖRÜK",
    "GÖKHAN ADALI",
    "VEDAT ÖZBAŞ",
    "HÜSEYİN GÜNER",
    "MAHİR KARABUĞA",
    "EBUBEKİR ŞILTAK",
    "MUSTAFA KAYNAK",
    "BÜLENT DOĞAN",
    "ZAFER ŞİRİN",
    "BERKANT YILDIZ",
    "VEYSEL TUAÇ",
    "ŞABETTİN KAYA",
    "TOLGAHAN CEYLAN",
    "AHMET KÖRBALTA",
    "OĞUZHAN ÖKSÜZ",
    "YAVUZ KORKMAZ",
    "İBRAHİM TEKDEMİR",
    "SAMET UMUT KAMSIZ",
    "MEHMET BUZ",
    "BİLAL ÇİMEN",
    "MUHARREM EKİN",
    "METİN HACIOĞLU",
    "EKREM ÇELİK",
    "MEHMET OLCAY",
    "AYDIN AKBIYIK",
    "BAYRAM KAPLAN",
    "FUAT BOZTEPE",
    "FETHİ KAYA",
    "MEHMET ŞİRİN ELİŞ",
    "SERCAN KARAKILIÇ",
    "SEYİTHAN ESATOĞLU",
    "SERDAR ALÇO",
    "CEM KARAKILIÇ",
    "EROL YILMAZ",
    "SEDAT ÇOLAK",
    "CEMAL KARAKAYA",
    "BURAK ÇAKIR",
    "KUBİLAY YILMAZ",
    "HALİL İLKTAŞ",
    "MEHMET KAYA",
    "AHMET PETEK",
    "KUBİLAY ANAVATAN",
    "HÜSEYİN ÖZTÜRK",
    "MÜCAHİT ŞİŞMAN",
    "BERKAY ŞAHİN",
    "DURAN KARAKIŞ",
    "ENGİN ÖZGÜL",
    "YUNUS EMRE ERDEM",
    "HÜSEYİN DORUK",
    "YÜCEL DOĞAN",
    "OZAN ALTİNBAŞ",
    "MAHMUT SEYİTOĞLU",
    "TAMER ALÇO",
    "FATİH YERLİKAYA",
    "MERT YUMUK",
    "ABDULAZİZ GÜNEY",
    "MEHMET DİNDAR TAYURAK",
    "ALİ YILDIZ",
    "HALİL BÜYÜKARSLAN",
    "CUMA YALÇIN",
    "ABDULSELAM ARPACI",
    "MUSA ÖZER",
    "TOLGA KURU",
    "HÜSEYİN OMUSA KESKİN",
    "CİHAN ERGENER",
    "RAMAZAN ÇORAK",
    "EYÜP ALKAÇ",
    "YEMEN ADAR",
    "HÜRKAAN KAZAN",
    "VEYSEL YILDIZ",
    "OZAN KOLDEMİR",
    "HAŞİM YÜKSEL",
    "BARIŞ TOSUN",
    "METİN ACAR",
    "ENES YÖRENTİ",
    "ÖMER GÜNEŞ",
    "KENAN KARATAY",
    "TAMER İLHAN",
    "MEHMET TÜRK",
    "YASİN ÇELEBİ",
    "MÜJDAT KAYA",
    "EMRE KARAKAYA",
    "MEHMET SARAÇ",
    "BEKİR YILMAZ",
    "ÖMER HARUN GÜNEŞ",
    "AŞUR COŞAR",
    "EBUBEKİR BAY",
    "ERKAN ŞAHİN",
    "TAYFUN MİLDAN",
    "EMRULLAH ZENGİN",
    "İSA KESKİN",
    "RÜŞTÜ GÜLEN",
    "DOĞAN TÖNGEL",
    "FATİH ERDİN",
    "MEHMET ŞILTAK",
    "METİN AYDIN",
    "MUHAMMED TURSUN",
    "İSMAİL AYTEKİN",
    "CİHAN BARA",
    "AHMET IRMAK",
    "TOLGA ÖCAL",
    "SAİT GÖKMEN",
    "CİHAN SAĞ",
    "UMUT AYAS",
    "OKTAY ERDAL",
    "YILMAZ YASİN ÇELİK",
    "EMRE MÜDÜROĞLU",
    "SERDAR SEKENDÜR",
    "MAHMUT KOCAOĞLU",
    "KAMİL BOZTEPE",
    "ORKUN ARAS",
    "ALİ BAYRAM",
    "OSMAN ATAÇ",
    "MESUT ÇAKIR",
    "MESUT DOĞAN KARAGÖZ",
    "HÜSEYİN BEKDEMİR",
    "AHMET ERAY ÇELİK",
    "YASİN AKKUŞ",
    "RECEP ACAR",
    "SAVAŞ YEŞİL",
    "CİHAN DAĞKUŞU",
    "MEHMET SAİT YALMAN",
    "MEVLÜT AYAZ",
    "HABİB BALCİ",
    "TURGAY ARIKAN",
    "BAYRAM EFE"
]

DEFAULT_SHIFTS = [
    "08:00 - 16:00",
    "16:00 - 00:00",
    "00:00 - 08:00",
    "07:00 - 15:00",
    "09:00 - 17:00",
    "12:00 - 20:00",
    "Vardiya A",
    "Vardiya B",
    "Vardiya C",
    "Özel Vardiya",
]


# -----------------------------
# Sayfa ayarı
# -----------------------------
st.set_page_config(
    page_title="Çelebi Driver Panel",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Yardımcı fonksiyonlar
# -----------------------------
def normalize_name(value: str) -> str:
    return " ".join(str(value).strip().upper().split())


def normalize_plate(value: str) -> str:
    return " ".join(str(value).strip().upper().replace("-", "-").split())


def connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def execute(query: str, params: Iterable = ()) -> None:
    with connect() as conn:
        conn.execute(query, tuple(params))
        conn.commit()


def executemany(query: str, params: Iterable[Iterable]) -> None:
    with connect() as conn:
        conn.executemany(query, params)
        conn.commit()


def read_df(query: str, params: Iterable = ()) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=tuple(params))


def fetch_one(query: str, params: Iterable = ()):
    with connect() as conn:
        return conn.execute(query, tuple(params)).fetchone()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL UNIQUE,
                group_id INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(group_id) REFERENCES groups(id)
            );

            CREATE TABLE IF NOT EXISTS shift_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date TEXT NOT NULL,
                driver_id INTEGER NOT NULL,
                shift TEXT NOT NULL,
                plate TEXT NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(driver_id) REFERENCES drivers(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_shift_logs_date ON shift_logs(log_date);
            CREATE INDEX IF NOT EXISTS idx_shift_logs_driver ON shift_logs(driver_id);
            CREATE INDEX IF NOT EXISTS idx_shift_logs_shift ON shift_logs(shift);
            CREATE INDEX IF NOT EXISTS idx_shift_logs_plate ON shift_logs(plate);
            """
        )

        group_count = conn.execute("SELECT COUNT(*) FROM groups").fetchone()[0]
        if group_count == 0:
            conn.executemany(
                "INSERT INTO groups (name, description) VALUES (?, ?)",
                INITIAL_GROUPS,
            )

        default_group_id = conn.execute(
            "SELECT id FROM groups WHERE name = ?", ("Genel Sürücüler",)
        ).fetchone()[0]

        driver_count = conn.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
        if driver_count == 0:
            conn.executemany(
                "INSERT OR IGNORE INTO drivers (full_name, group_id, active) VALUES (?, ?, 1)",
                [(normalize_name(name), default_group_id) for name in INITIAL_DRIVERS],
            )
        conn.commit()


@st.cache_data(show_spinner=False)
def image_to_base64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode("utf-8")


def inject_css(theme: str) -> None:
    dark = theme == "Koyu"
    palette = {
        "bg": "#0B0F14" if dark else "#F6F7F9",
        "surface": "#111827" if dark else "#FFFFFF",
        "surface2": "#182130" if dark else "#F1F3F6",
        "text": "#F8FAFC" if dark else "#111111",
        "muted": "#B6BEC9" if dark else "#555E6B",
        "border": "#2D3748" if dark else "#E3E6EA",
        "accent": "#FFFFFF" if dark else "#111111",
        "accent2": "#9CA3AF" if dark else "#3A3A3A",
    }
    primary_button_text = "#111111" if dark else "#FFFFFF"

    st.markdown(
        f"""
        <style>
            :root {{
                --c-bg: {palette['bg']};
                --c-surface: {palette['surface']};
                --c-surface2: {palette['surface2']};
                --c-text: {palette['text']};
                --c-muted: {palette['muted']};
                --c-border: {palette['border']};
                --c-accent: {palette['accent']};
                --c-accent2: {palette['accent2']};
            }}
            .stApp {{
                background: radial-gradient(circle at top left, var(--c-surface2) 0, var(--c-bg) 38%, var(--c-bg) 100%);
                color: var(--c-text);
            }}
            [data-testid="stSidebar"] {{
                background: var(--c-surface);
                border-right: 1px solid var(--c-border);
            }}
            [data-testid="stMetric"] {{
                background: var(--c-surface);
                border: 1px solid var(--c-border);
                padding: 16px;
                border-radius: 18px;
                box-shadow: 0 8px 24px rgba(0,0,0,.06);
            }}
            .block-container {{
                padding-top: 1.2rem;
                padding-bottom: 3rem;
                max-width: 1450px;
            }}
            h1, h2, h3, h4, h5, h6, p, span, div {{
                font-family: "Inter", "Segoe UI", Arial, sans-serif;
            }}
            .hero-card {{
                background: linear-gradient(135deg, var(--c-surface), var(--c-surface2));
                border: 1px solid var(--c-border);
                border-radius: 26px;
                padding: 26px 28px;
                margin: 0 0 22px 0;
                box-shadow: 0 16px 34px rgba(0,0,0,.08);
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 22px;
            }}
            .hero-left {{ display: flex; align-items: center; gap: 18px; }}
            .hero-logo {{
                width: 124px;
                max-height: 82px;
                object-fit: contain;
                border-radius: 12px;
                background: #fff;
                padding: 8px;
                border: 1px solid var(--c-border);
            }}
            .hero-title {{
                font-size: 28px;
                font-weight: 800;
                color: var(--c-text);
                margin: 0 0 4px 0;
                letter-spacing: -0.02em;
            }}
            .hero-subtitle {{
                color: var(--c-muted);
                font-size: 14px;
                margin: 0;
            }}
            .pill {{
                border: 1px solid var(--c-border);
                color: var(--c-text);
                background: var(--c-surface);
                padding: 8px 12px;
                border-radius: 999px;
                font-size: 13px;
                white-space: nowrap;
            }}
            .section-card {{
                background: var(--c-surface);
                border: 1px solid var(--c-border);
                border-radius: 22px;
                padding: 20px;
                margin-bottom: 16px;
                box-shadow: 0 10px 28px rgba(0,0,0,.055);
            }}
            .soft-note {{
                color: var(--c-muted);
                font-size: 13px;
                padding: 10px 12px;
                border-radius: 12px;
                border: 1px solid var(--c-border);
                background: var(--c-surface2);
            }}
            div[data-testid="stDataFrame"] {{
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--c-border);
            }}
            .stButton>button, .stDownloadButton>button {{
                border-radius: 13px;
                border: 1px solid var(--c-border);
                font-weight: 700;
            }}
            .stButton>button[kind="primary"] {{
                background: var(--c-accent);
                color: {primary_button_text};
            }}
            @media (max-width: 780px) {{
                .hero-card {{
                    flex-direction: column;
                    align-items: flex-start;
                    padding: 18px;
                }}
                .hero-left {{ flex-direction: column; align-items: flex-start; }}
                .hero-title {{ font-size: 22px; }}
                .hero-logo {{ width: 104px; }}
                .pill {{ white-space: normal; }}
                .block-container {{ padding-left: 0.9rem; padding-right: 0.9rem; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_header(title: str, subtitle: str) -> None:
    logo64 = image_to_base64(str(LOGO_PATH))
    img_html = f'<img class="hero-logo" src="data:image/png;base64,{logo64}" />' if logo64 else ""
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-left">
                {img_html}
                <div>
                    <div class="hero-title">{title}</div>
                    <p class="hero-subtitle">{subtitle}</p>
                </div>
            </div>
            <div class="pill">SQLite kayıt sistemi · Streamlit panel · Mobil uyumlu</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_groups_df() -> pd.DataFrame:
    return read_df("SELECT id, name, description FROM groups ORDER BY id")


def get_driver_df(include_passive: bool = True) -> pd.DataFrame:
    where = "" if include_passive else "WHERE d.active = 1"
    return read_df(
        f"""
        SELECT
            d.id,
            d.full_name AS 'Sürücü',
            g.name AS 'Grup',
            CASE WHEN d.active = 1 THEN 'Aktif' ELSE 'Pasif' END AS 'Durum',
            d.phone AS 'Telefon',
            d.notes AS 'Not',
            d.created_at AS 'Eklenme Zamanı'
        FROM drivers d
        LEFT JOIN groups g ON g.id = d.group_id
        {where}
        ORDER BY d.active DESC, d.full_name ASC
        """
    )


def get_driver_options(active_only: bool = True) -> list[dict]:
    where = "WHERE d.active = 1" if active_only else ""
    df = read_df(
        f"""
        SELECT d.id, d.full_name, g.name AS group_name, d.active
        FROM drivers d
        LEFT JOIN groups g ON g.id = d.group_id
        {where}
        ORDER BY d.full_name
        """
    )
    return df.to_dict("records")


def get_shift_logs(
    start: Optional[date] = None,
    end: Optional[date] = None,
    driver_id: Optional[int] = None,
    group_id: Optional[int] = None,
    shift: Optional[str] = None,
    plate_contains: str = "",
    include_passive: bool = True,
) -> pd.DataFrame:
    clauses = []
    params: list = []
    if start:
        clauses.append("l.log_date >= ?")
        params.append(start.isoformat())
    if end:
        clauses.append("l.log_date <= ?")
        params.append(end.isoformat())
    if driver_id:
        clauses.append("d.id = ?")
        params.append(driver_id)
    if group_id:
        clauses.append("g.id = ?")
        params.append(group_id)
    if shift and shift != "Tümü":
        clauses.append("l.shift = ?")
        params.append(shift)
    if plate_contains.strip():
        clauses.append("UPPER(l.plate) LIKE ?")
        params.append(f"%{normalize_plate(plate_contains)}%")
    if not include_passive:
        clauses.append("d.active = 1")

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return read_df(
        f"""
        SELECT
            l.id AS 'Kayıt ID',
            l.log_date AS 'Tarih',
            d.full_name AS 'Sürücü',
            g.name AS 'Grup',
            l.shift AS 'Vardiya',
            l.plate AS 'Araç Plakası',
            l.note AS 'Not',
            CASE WHEN d.active = 1 THEN 'Aktif' ELSE 'Pasif' END AS 'Sürücü Durumu',
            l.created_at AS 'Kayıt Zamanı'
        FROM shift_logs l
        JOIN drivers d ON d.id = l.driver_id
        LEFT JOIN groups g ON g.id = d.group_id
        {where}
        ORDER BY l.log_date DESC, l.created_at DESC, d.full_name ASC
        """,
        params,
    )


def filter_driver_table(df: pd.DataFrame, search: str, status: str, group: str) -> pd.DataFrame:
    out = df.copy()
    if search.strip():
        mask = out.apply(lambda row: search.upper() in " ".join(map(str, row.values)).upper(), axis=1)
        out = out[mask]
    if status != "Tümü":
        out = out[out["Durum"] == status]
    if group != "Tümü":
        out = out[out["Grup"] == group]
    return out


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Rapor") -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        worksheet = writer.sheets[sheet_name[:31]]
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 12), 42)
    return output.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def try_register_pdf_font() -> str:
    if SimpleDocTemplate is None:
        return "Helvetica"
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        str(BASE_DIR / "assets" / "DejaVuSans.ttf"),
    ]
    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("LocalSans", font_path))
                return "LocalSans"
            except Exception:
                continue
    return "Helvetica"


def to_pdf_bytes(df: pd.DataFrame, title: str) -> bytes:
    if SimpleDocTemplate is None:
        raise RuntimeError("PDF çıktısı için reportlab paketinin kurulu olması gerekir.")

    output = BytesIO()
    font_name = try_register_pdf_font()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=1.0 * cm,
        rightMargin=1.0 * cm,
        topMargin=1.0 * cm,
        bottomMargin=1.0 * cm,
    )
    styles = getSampleStyleSheet()
    styles["Title"].fontName = font_name
    styles["Normal"].fontName = font_name

    display_df = df.head(500).copy()
    for col in display_df.columns:
        display_df[col] = display_df[col].astype(str).str.slice(0, 55)

    table_data = [display_df.columns.tolist()] + display_df.values.tolist()
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111111")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9D9D9")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story = [
        Paragraph(title, styles["Title"]),
        Paragraph(f"Oluşturulma zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles["Normal"]),
        Paragraph(f"Toplam kayıt: {len(df)} | PDF'te ilk {len(display_df)} kayıt gösterilir.", styles["Normal"]),
        Spacer(1, 0.35 * cm),
        table,
    ]
    doc.build(story)
    return output.getvalue()


def show_downloads(df: pd.DataFrame, prefix: str) -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Excel indir (.xlsx)",
            data=to_excel_bytes(df, "Rapor"),
            file_name=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "CSV indir",
            data=to_csv_bytes(df),
            file_name=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c3:
        if SimpleDocTemplate is None:
            st.button("PDF için reportlab gerekli", disabled=True, use_container_width=True)
        else:
            st.download_button(
                "PDF indir",
                data=to_pdf_bytes(df, "Çelebi Vardiya ve Araç Raporu"),
                file_name=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


def sidebar_logo() -> None:
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), use_container_width=True)
    st.sidebar.markdown("---")


def chart_or_info(df: pd.DataFrame, chart_type: str, title: str, x: str, y: str | None = None):
    if df.empty:
        st.info("Bu grafik için yeterli kayıt yok.")
        return
    if px is None:
        if y and x in df and y in df:
            st.bar_chart(df.set_index(x)[y])
        else:
            st.dataframe(df, use_container_width=True)
        return
    if chart_type == "bar":
        fig = px.bar(df, x=x, y=y, title=title, text_auto=True)
    elif chart_type == "line":
        fig = px.line(df, x=x, y=y, title=title, markers=True)
    else:
        fig = px.pie(df, names=x, values=y, title=title)
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), height=390)
    st.plotly_chart(fig, use_container_width=True)


# -----------------------------
# Sayfalar
# -----------------------------
def page_dashboard() -> None:
    render_header(
        "Operasyon Ana Sayfası",
        "Günlük sürücü-vardiya-plaka kayıtlarını tek ekrandan takip et.",
    )

    today = date.today().isoformat()
    total_driver = fetch_one("SELECT COUNT(*) FROM drivers")[0]
    active_driver = fetch_one("SELECT COUNT(*) FROM drivers WHERE active = 1")[0]
    today_logs = fetch_one("SELECT COUNT(*) FROM shift_logs WHERE log_date = ?", (today,))[0]
    unique_vehicles = fetch_one("SELECT COUNT(DISTINCT plate) FROM shift_logs")[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Sürücü", total_driver)
    c2.metric("Aktif Sürücü", active_driver)
    c3.metric("Bugünkü Kayıt", today_logs)
    c4.metric("Kayıtlı Araç Plakası", unique_vehicles or 0)

    st.markdown("### Bugünkü Operasyon")
    today_df = get_shift_logs(date.today(), date.today())
    if today_df.empty:
        st.info("Bugün için henüz vardiya/plaka kaydı girilmedi.")
    else:
        st.dataframe(today_df, use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)
    with col_a:
        shift_counts = read_df(
            """
            SELECT shift AS Vardiya, COUNT(*) AS Kayıt
            FROM shift_logs
            WHERE log_date >= ?
            GROUP BY shift
            ORDER BY Kayıt DESC
            """,
            ((date.today() - timedelta(days=30)).isoformat(),),
        )
        chart_or_info(shift_counts, "bar", "Son 30 Gün Vardiya Dağılımı", "Vardiya", "Kayıt")
    with col_b:
        group_counts = read_df(
            """
            SELECT g.name AS Grup, COUNT(*) AS Kayıt
            FROM shift_logs l
            JOIN drivers d ON d.id = l.driver_id
            JOIN groups g ON g.id = d.group_id
            WHERE l.log_date >= ?
            GROUP BY g.name
            ORDER BY Kayıt DESC
            """,
            ((date.today() - timedelta(days=30)).isoformat(),),
        )
        chart_or_info(group_counts, "pie", "Son 30 Gün Grup Dağılımı", "Grup", "Kayıt")

    st.markdown("### Hızlı Kontrol")
    st.markdown(
        """
        <div class="soft-note">
        Bu panel şu an manuel veri girişine göre çalışır. Streamlit Cloud üzerinde veri kalıcılığı sınırlı olabilir; gerçek operasyon kullanımı için sonraki adımda PostgreSQL/Supabase entegrasyonu önerilir.
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_driver_management() -> None:
    render_header(
        "Sürücü Yönetimi",
        "Sürücü ekle, grup değiştir, pasife al veya geçmişi bozmadan personel listesini yönet.",
    )

    groups = get_groups_df()
    drivers = get_driver_df(include_passive=True)
    group_names = ["Tümü"] + groups["name"].tolist()

    tab_list, tab_add, tab_edit, tab_groups = st.tabs(
        ["Liste", "Yeni Sürücü Ekle", "Düzenle / Pasif-Sil", "Grup Yönetimi"]
    )

    with tab_list:
        f1, f2, f3 = st.columns([2, 1, 1])
        search = f1.text_input("Sürücü, plaka, not veya grup içinde ara", key="driver_search")
        status = f2.selectbox("Durum", ["Tümü", "Aktif", "Pasif"], key="driver_status")
        group_filter = f3.selectbox("Grup", group_names, key="driver_group_filter")
        filtered = filter_driver_table(drivers, search, status, group_filter)

        st.caption(f"Gösterilen sürücü: {len(filtered)} / {len(drivers)}")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        show_downloads(filtered, "surucu_listesi")

    with tab_add:
        with st.form("add_driver_form", clear_on_submit=True):
            st.subheader("Yeni sürücü ekle")
            name = st.text_input("Ad Soyad", placeholder="Örn: AHMET YILMAZ")
            c1, c2 = st.columns(2)
            group_name = c1.selectbox("Personel Grubu", groups["name"].tolist())
            phone = c2.text_input("Telefon / Dahili (opsiyonel)")
            notes = st.text_area("Not (opsiyonel)")
            submitted = st.form_submit_button("Sürücüyü ekle", type="primary", use_container_width=True)

        if submitted:
            clean_name = normalize_name(name)
            if not clean_name:
                st.error("Ad Soyad boş bırakılamaz.")
            elif fetch_one("SELECT id FROM drivers WHERE full_name = ?", (clean_name,)):
                st.warning("Bu isimde bir sürücü zaten kayıtlı.")
            else:
                group_id = int(groups.loc[groups["name"] == group_name, "id"].iloc[0])
                execute(
                    "INSERT INTO drivers (full_name, group_id, active, phone, notes) VALUES (?, ?, 1, ?, ?)",
                    (clean_name, group_id, phone.strip(), notes.strip()),
                )
                st.success(f"{clean_name} sisteme eklendi.")
                st.rerun()

    with tab_edit:
        st.subheader("Sürücü bilgisi güncelle")
        options = get_driver_options(active_only=False)
        if not options:
            st.info("Henüz sürücü yok.")
        else:
            label_map = {
                f"{row['full_name']} · {row['group_name']} · {'Aktif' if row['active'] else 'Pasif'}": row
                for row in options
            }
            selected_label = st.selectbox("Sürücü seç", list(label_map.keys()))
            selected = label_map[selected_label]
            current = read_df("SELECT * FROM drivers WHERE id = ?", (selected["id"],)).iloc[0]

            with st.form("edit_driver_form"):
                new_name = st.text_input("Ad Soyad", value=current["full_name"])
                c1, c2, c3 = st.columns(3)
                group_names_only = groups["name"].tolist()
                current_group_name = read_df("SELECT name FROM groups WHERE id = ?", (int(current["group_id"]),)).iloc[0, 0]
                new_group = c1.selectbox(
                    "Grup",
                    group_names_only,
                    index=group_names_only.index(current_group_name),
                )
                new_status = c2.selectbox("Durum", ["Aktif", "Pasif"], index=0 if int(current["active"]) else 1)
                new_phone = c3.text_input("Telefon", value=current["phone"] or "")
                new_notes = st.text_area("Not", value=current["notes"] or "")
                save_update = st.form_submit_button("Değişiklikleri kaydet", type="primary", use_container_width=True)

            if save_update:
                clean_name = normalize_name(new_name)
                duplicate = fetch_one(
                    "SELECT id FROM drivers WHERE full_name = ? AND id <> ?",
                    (clean_name, int(current["id"])),
                )
                if not clean_name:
                    st.error("Ad Soyad boş bırakılamaz.")
                elif duplicate:
                    st.error("Bu isim başka bir sürücüde kayıtlı.")
                else:
                    new_group_id = int(groups.loc[groups["name"] == new_group, "id"].iloc[0])
                    execute(
                        """
                        UPDATE drivers
                        SET full_name = ?, group_id = ?, active = ?, phone = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (clean_name, new_group_id, 1 if new_status == "Aktif" else 0, new_phone.strip(), new_notes.strip(), int(current["id"])),
                    )
                    st.success("Sürücü bilgisi güncellendi.")
                    st.rerun()

            st.markdown("---")
            st.subheader("Pasife alma / kalıcı silme")
            log_count = fetch_one("SELECT COUNT(*) FROM shift_logs WHERE driver_id = ?", (int(current["id"]),))[0]
            st.caption(f"Bu sürücüye bağlı geçmiş kayıt sayısı: {log_count}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sürücüyü pasife al", use_container_width=True):
                    execute("UPDATE drivers SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (int(current["id"]),))
                    st.success("Sürücü pasife alındı. Geçmiş kayıtlar korunur.")
                    st.rerun()
            with c2:
                confirm_delete = st.checkbox("Kalıcı silmeyi onaylıyorum", key="confirm_driver_delete")
                if st.button("Kalıcı sil", disabled=(not confirm_delete or log_count > 0), use_container_width=True):
                    execute("DELETE FROM drivers WHERE id = ?", (int(current["id"]),))
                    st.success("Sürücü kalıcı olarak silindi.")
                    st.rerun()
                if log_count > 0:
                    st.caption("Geçmiş kaydı olan sürücü kalıcı silinemez; pasife alınmalıdır.")

    with tab_groups:
        st.subheader("10 Grup Tanımı")
        st.caption("Operasyon yapısını bozmamak için sistem 10 grup mantığıyla başlar; grup isim ve açıklamaları buradan değiştirilebilir.")
        st.dataframe(groups, use_container_width=True, hide_index=True)

        group_label_map = {f"{row['id']} · {row['name']}": row for _, row in groups.iterrows()}
        selected_group_label = st.selectbox("Düzenlenecek grup", list(group_label_map.keys()))
        selected_group = group_label_map[selected_group_label]

        with st.form("group_edit_form"):
            new_group_name = st.text_input("Grup adı", value=selected_group["name"])
            new_desc = st.text_area("Açıklama", value=selected_group["description"] or "")
            save_group = st.form_submit_button("Grubu güncelle", type="primary", use_container_width=True)

        if save_group:
            clean_group = " ".join(new_group_name.strip().split())
            if not clean_group:
                st.error("Grup adı boş bırakılamaz.")
            else:
                duplicate = fetch_one(
                    "SELECT id FROM groups WHERE name = ? AND id <> ?",
                    (clean_group, int(selected_group["id"])),
                )
                if duplicate:
                    st.error("Bu grup adı zaten kullanılıyor.")
                else:
                    execute(
                        "UPDATE groups SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (clean_group, new_desc.strip(), int(selected_group["id"])),
                    )
                    st.success("Grup güncellendi.")
                    st.rerun()


def page_shift_entry() -> None:
    render_header(
        "Canlı Vardiya ve Araç Girişi",
        "Amirler günlük operasyon için sürücü, vardiya ve plaka eşleşmesini buradan işler.",
    )

    groups = get_groups_df()
    drivers = get_driver_options(active_only=True)
    if not drivers:
        st.warning("Aktif sürücü bulunamadı. Önce Sürücü Yönetimi sayfasından sürücü ekleyin veya aktife alın.")
        return

    st.markdown("### Tekil kayıt girişi")
    with st.form("single_log_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([1, 1, 2])
        log_date = c1.date_input("Tarih", value=date.today(), format="DD.MM.YYYY")
        shift = c2.selectbox("Vardiya", DEFAULT_SHIFTS)
        if shift == "Özel Vardiya":
            shift = c2.text_input("Özel vardiya yaz", placeholder="Örn: 10:00 - 18:00")

        driver_labels = [f"{d['full_name']} · {d['group_name']}" for d in drivers]
        driver_lookup = {f"{d['full_name']} · {d['group_name']}": d for d in drivers}
        selected_driver_label = c3.selectbox("Sürücü seçimi", driver_labels)
        c4, c5 = st.columns([1, 2])
        plate = c4.text_input("Araç plakası", placeholder="34 LMN 123 veya APR-45")
        note = c5.text_input("Not (opsiyonel)", placeholder="Örn: VIP görev, bagaj transferi")
        submitted = st.form_submit_button("Vardiya kaydını ekle", type="primary", use_container_width=True)

    if submitted:
        selected_driver = driver_lookup[selected_driver_label]
        clean_plate = normalize_plate(plate)
        clean_shift = " ".join(str(shift).strip().split())
        if not clean_shift:
            st.error("Vardiya bilgisi boş bırakılamaz.")
        elif not clean_plate:
            st.error("Araç plakası boş bırakılamaz.")
        else:
            execute(
                "INSERT INTO shift_logs (log_date, driver_id, shift, plate, note) VALUES (?, ?, ?, ?, ?)",
                (log_date.isoformat(), int(selected_driver["id"]), clean_shift, clean_plate, note.strip()),
            )
            st.success("Vardiya ve araç kaydı eklendi.")
            st.rerun()

    st.markdown("---")
    st.markdown("### Toplu kayıt girişi")
    st.caption("Aynı tarih için birden fazla sürücü kaydını hızlı girmek için tabloyu doldur.")

    driver_name_options = [d["full_name"] for d in drivers]
    batch_date = st.date_input("Toplu kayıt tarihi", value=date.today(), format="DD.MM.YYYY", key="batch_date")
    initial_batch = pd.DataFrame(
        [{"Sürücü": "", "Vardiya": "", "Araç Plakası": "", "Not": ""} for _ in range(5)]
    )
    edited = st.data_editor(
        initial_batch,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sürücü": st.column_config.SelectboxColumn("Sürücü", options=[""] + driver_name_options, required=False),
            "Vardiya": st.column_config.SelectboxColumn("Vardiya", options=[""] + DEFAULT_SHIFTS[:-1], required=False),
            "Araç Plakası": st.column_config.TextColumn("Araç Plakası"),
            "Not": st.column_config.TextColumn("Not"),
        },
        key="batch_editor",
    )
    if st.button("Toplu kayıtları kaydet", type="primary", use_container_width=True):
        driver_id_by_name = {d["full_name"]: int(d["id"]) for d in drivers}
        rows_to_insert = []
        skipped = 0
        for _, row in edited.iterrows():
            dname = str(row.get("Sürücü", "")).strip()
            sh = str(row.get("Vardiya", "")).strip()
            pl = normalize_plate(row.get("Araç Plakası", ""))
            nt = str(row.get("Not", "")).strip()
            if not dname and not sh and not pl:
                continue
            if dname in driver_id_by_name and sh and pl:
                rows_to_insert.append((batch_date.isoformat(), driver_id_by_name[dname], sh, pl, nt))
            else:
                skipped += 1
        if rows_to_insert:
            executemany(
                "INSERT INTO shift_logs (log_date, driver_id, shift, plate, note) VALUES (?, ?, ?, ?, ?)",
                rows_to_insert,
            )
            st.success(f"{len(rows_to_insert)} kayıt eklendi. Eksik olduğu için atlanan satır: {skipped}")
            st.rerun()
        else:
            st.warning("Kaydedilecek geçerli satır bulunamadı.")

    st.markdown("---")
    st.markdown("### Bugünkü kayıtlar")
    today_df = get_shift_logs(date.today(), date.today())
    st.dataframe(today_df, use_container_width=True, hide_index=True)


def page_history() -> None:
    render_header(
        "Geçmiş Loglar ve Filtreleme",
        "Tarih, sürücü, grup, vardiya ve plaka filtrelerini birlikte kullanarak geçmiş operasyonu incele.",
    )

    groups = get_groups_df()
    drivers = get_driver_options(active_only=False)
    all_shifts_df = read_df("SELECT DISTINCT shift FROM shift_logs ORDER BY shift")
    shift_options = ["Tümü"] + (all_shifts_df["shift"].tolist() if not all_shifts_df.empty else DEFAULT_SHIFTS[:-1])

    with st.expander("Filtreler", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        start_date = c1.date_input("Başlangıç", value=date.today() - timedelta(days=30), format="DD.MM.YYYY")
        end_date = c2.date_input("Bitiş", value=date.today(), format="DD.MM.YYYY")
        include_passive = c3.checkbox("Pasif sürücüleri dahil et", value=True)
        all_time = c4.checkbox("Tüm zamanlar", value=False)

        c5, c6, c7, c8 = st.columns(4)
        driver_label_options = ["Tümü"] + [f"{d['full_name']} · {d['group_name']}" for d in drivers]
        driver_label = c5.selectbox("Personel", driver_label_options)
        driver_id = None
        if driver_label != "Tümü":
            driver_id = int(drivers[driver_label_options.index(driver_label) - 1]["id"])

        group_label_options = ["Tümü"] + groups["name"].tolist()
        group_label = c6.selectbox("Grup", group_label_options)
        group_id = None if group_label == "Tümü" else int(groups.loc[groups["name"] == group_label, "id"].iloc[0])

        shift_filter = c7.selectbox("Vardiya", shift_options)
        plate_filter = c8.text_input("Plaka içinde ara")

    if start_date > end_date and not all_time:
        st.error("Başlangıç tarihi bitiş tarihinden büyük olamaz.")
        return

    df = get_shift_logs(
        start=None if all_time else start_date,
        end=None if all_time else end_date,
        driver_id=driver_id,
        group_id=group_id,
        shift=shift_filter,
        plate_contains=plate_filter,
        include_passive=include_passive,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filtrelenen Kayıt", len(df))
    c2.metric("Sürücü Sayısı", df["Sürücü"].nunique() if not df.empty else 0)
    c3.metric("Araç Plakası", df["Araç Plakası"].nunique() if not df.empty else 0)
    c4.metric("Vardiya Tipi", df["Vardiya"].nunique() if not df.empty else 0)

    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        show_downloads(df, "gecmis_loglar")

        st.markdown("---")
        st.subheader("Hatalı kaydı sil")
        st.caption("Sadece yanlış girilen log kayıtları için kullanılmalı. Sürücü geçmişini korumak adına personel silme yerine pasife alma önerilir.")
        record_labels = [
            f"{int(row['Kayıt ID'])} · {row['Tarih']} · {row['Sürücü']} · {row['Vardiya']} · {row['Araç Plakası']}"
            for _, row in df.iterrows()
        ]
        selected_record = st.selectbox("Silinecek kayıt", record_labels)
        selected_id = int(selected_record.split(" · ")[0])
        confirm = st.checkbox("Bu log kaydını silmeyi onaylıyorum")
        if st.button("Seçili log kaydını sil", disabled=not confirm, use_container_width=True):
            execute("DELETE FROM shift_logs WHERE id = ?", (selected_id,))
            st.success("Log kaydı silindi.")
            st.rerun()


def page_reports() -> None:
    render_header(
        "Analiz ve Raporlama",
        "Operasyon yoğunluğunu tarih, vardiya, grup ve araç bazında grafiklerle değerlendir.",
    )

    c1, c2 = st.columns(2)
    start_date = c1.date_input("Rapor başlangıç", value=date.today() - timedelta(days=30), format="DD.MM.YYYY", key="report_start")
    end_date = c2.date_input("Rapor bitiş", value=date.today(), format="DD.MM.YYYY", key="report_end")

    df = get_shift_logs(start_date, end_date)
    if df.empty:
        st.info("Seçilen tarih aralığında raporlanacak kayıt yok.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Kayıt", len(df))
    c2.metric("Aktif Gün", df["Tarih"].nunique())
    c3.metric("Sürücü", df["Sürücü"].nunique())
    c4.metric("Araç", df["Araç Plakası"].nunique())

    daily = df.groupby("Tarih", as_index=False).size().rename(columns={"size": "Kayıt"})
    shift = df.groupby("Vardiya", as_index=False).size().rename(columns={"size": "Kayıt"}).sort_values("Kayıt", ascending=False)
    group = df.groupby("Grup", as_index=False).size().rename(columns={"size": "Kayıt"}).sort_values("Kayıt", ascending=False)
    vehicles = df.groupby("Araç Plakası", as_index=False).size().rename(columns={"size": "Kullanım"}).sort_values("Kullanım", ascending=False).head(15)
    drivers = df.groupby("Sürücü", as_index=False).size().rename(columns={"size": "Kayıt"}).sort_values("Kayıt", ascending=False).head(15)

    col_a, col_b = st.columns(2)
    with col_a:
        chart_or_info(daily, "line", "Günlük Kayıt Akışı", "Tarih", "Kayıt")
    with col_b:
        chart_or_info(shift, "bar", "Vardiya Bazlı Dağılım", "Vardiya", "Kayıt")

    col_c, col_d = st.columns(2)
    with col_c:
        chart_or_info(group, "pie", "Grup Bazlı Dağılım", "Grup", "Kayıt")
    with col_d:
        chart_or_info(vehicles, "bar", "En Çok Kullanılan Araçlar", "Araç Plakası", "Kullanım")

    st.markdown("### En çok kayıt girilen sürücüler")
    st.dataframe(drivers, use_container_width=True, hide_index=True)

    st.markdown("### Rapor verisi")
    st.dataframe(df, use_container_width=True, hide_index=True)
    show_downloads(df, "analiz_raporu")


def page_settings() -> None:
    render_header(
        "Ayarlar ve Yedekleme",
        "Logo, veri tabanı, yedek dosyası ve kurulum durumunu kontrol et.",
    )

    st.markdown("### Sistem durumu")
    c1, c2, c3 = st.columns(3)
    c1.metric("SQLite DB", "Hazır" if DB_PATH.exists() else "Yok")
    c2.metric("Logo", "Hazır" if LOGO_PATH.exists() else "Yok")
    c3.metric("Sürücü Seed", len(INITIAL_DRIVERS))

    st.code(f"Veri tabanı yolu: {DB_PATH}")

    st.markdown("### Yedek indir")
    if DB_PATH.exists():
        st.download_button(
            "SQLite veri tabanı yedeğini indir",
            data=DB_PATH.read_bytes(),
            file_name=f"celebi_driver_panel_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.sqlite3",
            mime="application/octet-stream",
            use_container_width=True,
        )

    st.markdown("### Kurulum notu")
    st.markdown(
        """
        - GitHub/Streamlit Cloud için ana dosya yolu: `app.py`
        - Logonun yolu: `assets/celebi_logo.png`
        - Veriler varsayılan olarak `data/celebi_driver_panel.sqlite3` içinde tutulur.
        - Streamlit Cloud ücretsiz ortamda dosya sistemi kalıcı garanti vermez; gerçek operasyon kullanımı için sonraki sürümde Supabase/PostgreSQL önerilir.
        """
    )

    with st.expander("Tehlikeli alan: Veritabanını sıfırla"):
        st.warning("Bu işlem tüm vardiya loglarını siler ve başlangıç sürücü listesini yeniden kurar.")
        confirm_text = st.text_input("Sıfırlamak için SIFIRLA yaz")
        if st.button("Veritabanını sıfırla", disabled=confirm_text != "SIFIRLA", use_container_width=True):
            if DB_PATH.exists():
                DB_PATH.unlink()
            init_db()
            st.success("Veritabanı sıfırlandı.")
            st.rerun()


# -----------------------------
# Uygulama ana akışı
# -----------------------------
def main() -> None:
    init_db()
    sidebar_logo()
    theme = st.sidebar.selectbox("Tema", ["Açık", "Koyu"], index=0)
    inject_css(theme)

    st.sidebar.markdown("### Menü")
    page = st.sidebar.radio(
        "Sayfa seç",
        [
            "Ana Sayfa",
            "Sürücü Yönetimi",
            "Vardiya Girişi",
            "Geçmiş Loglar",
            "Analiz Raporları",
            "Ayarlar / Yedekleme",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Çelebi Hava Hizmetleri · Driver Shift Panel")

    if page == "Ana Sayfa":
        page_dashboard()
    elif page == "Sürücü Yönetimi":
        page_driver_management()
    elif page == "Vardiya Girişi":
        page_shift_entry()
    elif page == "Geçmiş Loglar":
        page_history()
    elif page == "Analiz Raporları":
        page_reports()
    else:
        page_settings()


if __name__ == "__main__":
    main()
