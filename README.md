# -*- coding: utf-8 -*-
"""
Çelebi Hava Hizmetleri - Sürücü Vardiya ve Araç Yönetim Paneli
Streamlit + Supabase PostgreSQL tek dosya uygulama.

Çalıştırma:
    pip install -r requirements.txt
    streamlit run app.py
"""

from __future__ import annotations

import base64
import os
import re
from contextlib import closing

import psycopg2
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
LOGO_PATH = BASE_DIR / "assets" / "celebi_logo.png"

SEED_VERSION = "2026-05-21-driver-ac-class-update-v11"
PLATE_SEED_VERSION = "2026-05-20-official-vehicle-plates-v5"
APP_BUILD_VERSION = "v14-streamlit-supabase-postgresql"
MANAGER_PAGES = [
    "Ana Sayfa",
    "Sürücü Yönetimi",
    "Plaka Yönetimi",
    "Vardiya Girişi",
    "Geçmiş Loglar",
    "Analiz Raporları",
    "Ayarlar / Yedekleme",
]
COORDINATOR_PAGES = [
    "Ana Sayfa",
    "Sürücü Yönetimi",
    "Plaka Yönetimi",
    "Vardiya Girişi",
]

INITIAL_VEHICLE_PLATES = [
    "TBTU000074",
    "TBTU000078",
    "TBTU000080",
    "TBTU000094",
    "TBTU000141",
    "TBTU000142",
    "TBTU000143",
    "TBTU000146",
    "TBTU000147",
    "TBTU000149",
    "TBTU000150",
    "TBTU000154",
    "TBTU000155",
    "TBTU000156",
    "TBTU000259",
    "TBTU000260",
    "TBTU000276",
    "TBTU000293",
    "TBTU000294",
    "TBTU000295",
    "TBTU000296",
    "TBTU000297",
    "TBTU000299",
    "TBTU000300",
    "TBTU000301",
    "TBTU000303",
    "TBTU000304",
    "TBTU000305",
    "TBTU000306",
    "TBTU000308",
    "TBTU000309",
    "TBTU000310",
    "TBTU000311",
    "TBTU000312",
    "TBTU000313",
    "TBTU000314",
    "TBTU000315",
    "TBTU000316",
    "TBTU000317",
    "TBTU000320",
    "TBTU000321",
    "TBTU000323",
    "TBTU000331",
    "TBTU000332",
    "TBTU000333",
    "TBTU000334",
    "TBTU000363",
    "TBTU000364",
    "TBTU000365",
    "TBTU000366",
    "TBTU000371",
    "TBTU000381",
    "TBTU900001",
]


OFFICIAL_DRIVER_GROUPS = [
    ('A SINIFI', 'A sınıfı sürücü grubunda görev yapan personel.'),
    ('C SINIFI', 'C sınıfı sürücü grubunda görev yapan personel.'),
    ('D SINIFI', 'D sınıfı sürücü grubunda görev yapan personel.'),
    ('KARGO TRAKTÖRÜ', 'Kargo traktörü kullanımı için tanımlı sürücüler.'),
    ('ŞUT TRAKTÖRÜ', 'Şut traktörü ve bagaj operasyonlarında görev alabilen sürücüler.'),
    ('RAMP EMNİYET EKİBİ', 'Ramp emniyet ekibinde görevli sürücü personel.'),
    ('FOLLOW ME', 'Follow Me operasyonunda görev alabilen sürücüler.'),
    ('TEMIZLIK_TRAKTOR', 'Temizlik traktörü operasyonu için tanımlı sürücüler.'),
    ('SINIF YÜKSELME EĞİTİMLERİ', 'Sınıf yükselme eğitim sürecinde takip edilen personel.'),
    ('Tanımlanmamış / Diğer', 'Grubu henüz netleşmeyen veya diğer kategoriye alınan personel.'),
]

# Eski sürümlerde kullanılan genel grup adları. V4 ilk açılışta kullanılmayanları temizler.
LEGACY_GROUP_NAMES = [
    'Genel Sürücüler',
    'VIP Sürücüleri',
    'Şut Altı / Bagaj Sürücüleri',
    'Apron Sürücüleri',
    'Ağır Vasıta',
    'Terminal Operasyon',
    'Uçak Altı Operasyon',
    'Transfer Sürücüleri',
    'Gece Operasyon',
    'Yedek / Takviye Ekip',
]

# Önceki dosyadaki yazım/split farklarını yeni resmi listeye bağlamak için kullanılır.
LEGACY_DRIVER_NAME_ALIASES = [
    ('MAZ_LUM İBRAHİM AKYOL', 'MAZLUM İBRAHİM AKYOL'),
    ('TOLGA KURU', 'TOLGA KURU HÜSEYİNO'),
    ('HÜSEYİN OMUSA KESKİN', 'MUSA KESKİN'),
    ('ÖMER HARUN GÜNEŞ', 'ÖMER HARUNGÜNEŞ'),
    ('UMUT AYAS', 'UMUT AYAS OKTAY'),
    ('OKTAY ERDAL', 'ERDAL YILMAZ'),
    ('YILMAZ YASİN ÇELİK', 'YASİN ÇELİK'),
]

INITIAL_GROUPS = OFFICIAL_DRIVER_GROUPS

INITIAL_DRIVER_GROUP_ASSIGNMENTS = [
    ('UMUT BOĞA', 'C SINIFI'),
    ('MAZLUM İBRAHİM AKYOL', 'C SINIFI'),
    ('MAHMUT KARADOĞAN', 'C SINIFI'),
    ('ÖMER ELE', 'C SINIFI'),
    ('TAYFUN ÜZÜM', 'A SINIFI'),
    ('MUHAMMET EFE BECİT', 'C SINIFI'),
    ('KENAN KANDO', 'C SINIFI'),
    ('İSA CEYLAN', 'C SINIFI'),
    ('DOĞAN KIŞLA', 'C SINIFI'),
    ('HEYBET KÖRÜK', 'C SINIFI'),
    ('GÖKHAN ADALI', 'C SINIFI'),
    ('VEDAT ÖZBAŞ', 'C SINIFI'),
    ('HÜSEYİN GÜNER', 'C SINIFI'),
    ('MAHİR KARABUĞA', 'C SINIFI'),
    ('EBUBEKİR ŞILTAK', 'C SINIFI'),
    ('MUSTAFA KAYNAK', 'C SINIFI'),
    ('BÜLENT DOĞAN', 'A SINIFI'),
    ('ZAFER ŞİRİN', 'C SINIFI'),
    ('BERKANT YILDIZ', 'C SINIFI'),
    ('VEYSEL TUAÇ', 'C SINIFI'),
    ('ŞABETTİN KAYA', 'C SINIFI'),
    ('TOLGAHAN CEYLAN', 'C SINIFI'),
    ('AHMET KÖRBALTA', 'C SINIFI'),
    ('OĞUZHAN ÖKSÜZ', 'A SINIFI'),
    ('YAVUZ KORKMAZ', 'A SINIFI'),
    ('İBRAHİM TEKDEMİR', 'C SINIFI'),
    ('SAMET UMUT KAMSIZ', 'C SINIFI'),
    ('MEHMET BUZ', 'C SINIFI'),
    ('BİLAL ÇİMEN', 'A SINIFI'),
    ('MUHARREM EKİN', 'C SINIFI'),
    ('METİN HACIOĞLU', 'A SINIFI'),
    ('EKREM ÇELİK', 'A SINIFI'),
    ('MEHMET OLCAY', 'C SINIFI'),
    ('AYDIN AKBIYIK', 'A SINIFI'),
    ('BAYRAM KAPLAN', 'C SINIFI'),
    ('FUAT BOZTEPE', 'C SINIFI'),
    ('FETHİ KAYA', 'C SINIFI'),
    ('MEHMET ŞİRİN ELİŞ', 'A SINIFI'),
    ('SERCAN KARAKILIÇ', 'A SINIFI'),
    ('SEYİTHAN ESATOĞLU', 'A SINIFI'),
    ('SERDAR ALÇO', 'A SINIFI'),
    ('CEM KARAKILIÇ', 'C SINIFI'),
    ('EROL YILMAZ', 'A SINIFI'),
    ('SEDAT ÇOLAK', 'C SINIFI'),
    ('CEMAL KARAKAYA', 'A SINIFI'),
    ('BURAK ÇAKIR', 'C SINIFI'),
    ('KUBİLAY YILMAZ', 'C SINIFI'),
    ('HALİL İLKTAŞ', 'A SINIFI'),
    ('MEHMET KAYA', 'C SINIFI'),
    ('AHMET PETEK', 'C SINIFI'),
    ('KUBİLAY ANAVATAN', 'C SINIFI'),
    ('HÜSEYİN ÖZTÜRK', 'C SINIFI'),
    ('MÜCAHİT ŞİŞMAN', 'A SINIFI'),
    ('BERKAY ŞAHİN', 'C SINIFI'),
    ('DURAN KARAKIŞ', 'A SINIFI'),
    ('ENGİN ÖZGÜL', 'C SINIFI'),
    ('YUNUS EMRE ERDEM', 'C SINIFI'),
    ('HÜSEYİN DORUK', 'C SINIFI'),
    ('YÜCEL DOĞAN', 'C SINIFI'),
    ('OZAN ALTİNBAŞ', 'C SINIFI'),
    ('MAHMUT SEYİTOĞLU', 'C SINIFI'),
    ('TAMER ALÇO', 'A SINIFI'),
    ('FATİH YERLİKAYA', 'C SINIFI'),
    ('MERT YUMUK', 'C SINIFI'),
    ('ABDULAZİZ GÜNEY', 'A SINIFI'),
    ('MEHMET DİNDAR TAYURAK', 'C SINIFI'),
    ('ALİ YILDIZ', 'A SINIFI'),
    ('HALİL BÜYÜKARSLAN', 'A SINIFI'),
    ('CUMA YALÇIN', 'C SINIFI'),
    ('ABDULSELAM ARPACI', 'C SINIFI'),
    ('MUSA ÖZER', 'C SINIFI'),
    ('TOLGA KURU HÜSEYİNO', 'A SINIFI'),
    ('MUSA KESKİN', 'C SINIFI'),
    ('CİHAN ERGENER', 'A SINIFI'),
    ('RAMAZAN ÇORAK', 'A SINIFI'),
    ('EYÜP ALKAÇ', 'C SINIFI'),
    ('YEMEN ADAR', 'A SINIFI'),
    ('HÜRKAAN KAZAN', 'A SINIFI'),
    ('VEYSEL YILDIZ', 'C SINIFI'),
    ('OZAN KOLDEMİR', 'C SINIFI'),
    ('HAŞİM YÜKSEL', 'A SINIFI'),
    ('BARIŞ TOSUN', 'A SINIFI'),
    ('METİN ACAR', 'C SINIFI'),
    ('ENES YÖRENTİ', 'C SINIFI'),
    ('ÖMER GÜNEŞ', 'C SINIFI'),
    ('KENAN KARATAY', 'C SINIFI'),
    ('TAMER İLHAN', 'C SINIFI'),
    ('MEHMET TÜRK', 'C SINIFI'),
    ('YASİN ÇELEBİ', 'C SINIFI'),
    ('MÜJDAT KAYA', 'C SINIFI'),
    ('EMRE KARAKAYA', 'C SINIFI'),
    ('MEHMET SARAÇ', 'C SINIFI'),
    ('BEKİR YILMAZ', 'C SINIFI'),
    ('ÖMER HARUNGÜNEŞ', 'C SINIFI'),
    ('AŞUR COŞAR', 'A SINIFI'),
    ('EBUBEKİR BAY', 'C SINIFI'),
    ('ERKAN ŞAHİN', 'C SINIFI'),
    ('TAYFUN MİLDAN', 'C SINIFI'),
    ('EMRULLAH ZENGİN', 'C SINIFI'),
    ('İSA KESKİN', 'C SINIFI'),
    ('RÜŞTÜ GÜLEN', 'A SINIFI'),
    ('DOĞAN TÖNGEL', 'A SINIFI'),
    ('FATİH ERDİN', 'C SINIFI'),
    ('MEHMET ŞILTAK', 'C SINIFI'),
    ('METİN AYDIN', 'A SINIFI'),
    ('MUHAMMED TURSUN', 'C SINIFI'),
    ('İSMAİL AYTEKİN', 'C SINIFI'),
    ('CİHAN BARA', 'C SINIFI'),
    ('AHMET IRMAK', 'A SINIFI'),
    ('TOLGA ÖCAL', 'C SINIFI'),
    ('SAİT GÖKMEN', 'A SINIFI'),
    ('CİHAN SAĞ', 'C SINIFI'),
    ('UMUT AYAS OKTAY', 'SINIF YÜKSELME EĞİTİMLERİ'),
    ('ERDAL YILMAZ', 'C SINIFI'),
    ('YASİN ÇELİK', 'C SINIFI'),
    ('EMRE MÜDÜROĞLU', 'C SINIFI'),
    ('SERDAR SEKENDÜR', 'SINIF YÜKSELME EĞİTİMLERİ'),
    ('MAHMUT KOCAOĞLU', 'A SINIFI'),
    ('KAMİL BOZTEPE', 'C SINIFI'),
    ('ORKUN ARAS', 'A SINIFI'),
    ('ALİ BAYRAM', 'C SINIFI'),
    ('OSMAN ATAÇ', 'C SINIFI'),
    ('MESUT ÇAKIR', 'A SINIFI'),
    ('MESUT DOĞAN KARAGÖZ', 'C SINIFI'),
    ('HÜSEYİN BEKDEMİR', 'C SINIFI'),
    ('AHMET ERAY ÇELİK', 'C SINIFI'),
    ('YASİN AKKUŞ', 'A SINIFI'),
    ('RECEP ACAR', 'A SINIFI'),
    ('SAVAŞ YEŞİL', 'SINIF YÜKSELME EĞİTİMLERİ'),
    ('CİHAN DAĞKUŞU', 'C SINIFI'),
    ('MEHMET SAİT YALMAN', 'C SINIFI'),
    ('MEVLÜT AYAZ', 'A SINIFI'),
    ('HABİB BALCİ', 'C SINIFI'),
    ('TURGAY ARIKAN', 'C SINIFI'),
    ('BAYRAM EFE', 'C SINIFI'),
    ('İBRAHİM DİNÇER', 'C SINIFI'),
    ('MUSTAFA SARIBAŞ', 'C SINIFI'),
    ('RAMAZAN BOZAN', 'C SINIFI'),
]

INITIAL_DRIVERS = [name for name, _group in INITIAL_DRIVER_GROUP_ASSIGNMENTS]

DEFAULT_SHIFTS = [
    "08:00 - 16:00",
    "16:00 - 00:00",
    "00:00 - 08:00",
    "07:00 - 15:00",
    "09:00 - 17:00",
    "12:00 - 20:00",
]

# V6: Vardiya artık serbest metin değil; giriş/çıkış saatleri 30 dakikalık seçeneklerden oluşturulur.
TIME_OPTIONS = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in range(0, 60, 5)]


def make_shift_label(start_time: str, end_time: str) -> str:
    return f"{start_time} - {end_time}"


def safe_time_index(value: str, fallback: str = "08:00") -> int:
    value = str(value or "").strip()
    if value in TIME_OPTIONS:
        return TIME_OPTIONS.index(value)
    return TIME_OPTIONS.index(fallback) if fallback in TIME_OPTIONS else 0


def parse_shift_label(shift: str) -> tuple[str, str]:
    clean = " ".join(str(shift or "").strip().split())
    # Beklenen format: HH:MM - HH:MM
    if " - " in clean:
        start, end = clean.split(" - ", 1)
        start = start.strip()
        end = end.strip()
        if start in TIME_OPTIONS and end in TIME_OPTIONS:
            return start, end
    return "08:00", "16:00"


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


def get_config_value(key: str, default: str = "") -> str:
    """Streamlit Secrets veya environment değişkeninden güvenli ayar okur."""
    value = None
    try:
        value = st.secrets.get(key)  # Streamlit Cloud Secrets
    except Exception:
        value = None
    if value is None:
        value = os.environ.get(key, default)
    return str(value).strip() if value is not None else default


def get_database_url() -> str:
    return get_config_value("DATABASE_URL") or get_config_value("SUPABASE_DATABASE_URL")


def mask_database_url(url: str) -> str:
    if not url:
        return "Tanımlı değil"
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", url)


def with_sslmode_require(url: str) -> str:
    """Supabase bağlantılarında SSL gerekli olduğu için eksikse sslmode=require ekler."""
    if not url:
        return url
    lowered = url.lower()
    if "sslmode=" in lowered:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}sslmode=require"


def to_pg_query(query: str) -> str:
    """Supabase PostgreSQL stilindeki bazı sorguları PostgreSQL uyumlu hale getirir."""
    q = query
    q = re.sub(r"AS\s+'([^']+)'", r'AS "\1"', q)
    q = q.replace("ORDER BY Kayıt", 'ORDER BY "Kayıt"')

    stripped = " ".join(q.strip().split())
    if stripped.startswith("INSERT OR IGNORE INTO vehicle_plates"):
        q = """
            INSERT INTO vehicle_plates (plate, active, notes)
            VALUES (%s, 1, %s)
            ON CONFLICT (plate) DO NOTHING
        """
    elif stripped.startswith("INSERT OR IGNORE INTO groups"):
        q = """
            INSERT INTO groups (name, description)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """
    else:
        q = q.replace("?", "%s")
    return q


class PostgresConnection:
    def __init__(self):
        database_url = get_database_url()
        if not database_url:
            raise RuntimeError("DATABASE_URL tanımlı değil. Streamlit Cloud > App > Settings > Secrets bölümüne DATABASE_URL eklenmeli.")
        self._conn = psycopg2.connect(with_sslmode_require(database_url))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                self._conn.rollback()
            else:
                self._conn.commit()
        finally:
            self._conn.close()
        return False

    def execute(self, query: str, params: Iterable = ()):  # sqlite benzeri kullanım için
        cur = self._conn.cursor()
        cur.execute(to_pg_query(query), tuple(params))
        return cur

    def executemany(self, query: str, params: Iterable[Iterable]):
        cur = self._conn.cursor()
        cur.executemany(to_pg_query(query), [tuple(p) for p in params])
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()


def connect() -> PostgresConnection:
    return PostgresConnection()


def execute(query: str, params: Iterable = ()) -> None:
    with connect() as conn:
        conn.execute(query, tuple(params))
        conn.commit()


def executemany(query: str, params: Iterable[Iterable]) -> None:
    with connect() as conn:
        conn.executemany(query, params)
        conn.commit()


def read_df(query: str, params: Iterable = ()) -> pd.DataFrame:
    database_url = get_database_url()
    if not database_url:
        return pd.DataFrame()
    with closing(psycopg2.connect(with_sslmode_require(database_url))) as conn:
        return pd.read_sql_query(to_pg_query(query), conn, params=tuple(params))


def fetch_one(query: str, params: Iterable = ()):
    with connect() as conn:
        cur = conn.execute(query, tuple(params))
        return cur.fetchone()


def table_columns(conn: PostgresConnection, table_name: str) -> set[str]:
    cur = conn.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table_name,),
    )
    return {row[0] for row in cur.fetchall()}


def init_db() -> None:
    """Supabase PostgreSQL tablolarını oluşturur ve başlangıç verilerini yükler."""
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS drivers (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL UNIQUE,
                group_id INTEGER NOT NULL REFERENCES groups(id),
                active INTEGER NOT NULL DEFAULT 1,
                phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shift_logs (
                id SERIAL PRIMARY KEY,
                log_date TEXT NOT NULL,
                driver_id INTEGER NOT NULL REFERENCES drivers(id) ON DELETE RESTRICT,
                shift TEXT NOT NULL,
                plate TEXT NOT NULL,
                vehicle_take_time TEXT DEFAULT '',
                vehicle_drop_time TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vehicle_plates (
                id SERIAL PRIMARY KEY,
                plate TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                notes TEXT DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_plates_plate ON vehicle_plates(plate)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vehicle_plates_active ON vehicle_plates(active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shift_logs_date ON shift_logs(log_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shift_logs_driver ON shift_logs(driver_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shift_logs_shift ON shift_logs(shift)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_shift_logs_plate ON shift_logs(plate)")

        shift_cols = table_columns(conn, "shift_logs")
        if "vehicle_take_time" not in shift_cols:
            conn.execute("ALTER TABLE shift_logs ADD COLUMN vehicle_take_time TEXT DEFAULT ''")
        if "vehicle_drop_time" not in shift_cols:
            conn.execute("ALTER TABLE shift_logs ADD COLUMN vehicle_drop_time TEXT DEFAULT ''")

        plate_seed_row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            ("vehicle_plate_seed_version",),
        ).fetchone()
        plate_seed_already_applied = bool(plate_seed_row and plate_seed_row[0] == PLATE_SEED_VERSION)
        if not plate_seed_already_applied:
            conn.executemany(
                "INSERT OR IGNORE INTO vehicle_plates (plate, active, notes) VALUES (?, 1, ?)",
                [(normalize_plate(plate), "Başlangıç resmi plaka listesi") for plate in INITIAL_VEHICLE_PLATES],
            )
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                ("vehicle_plate_seed_version", PLATE_SEED_VERSION),
            )

        existing_log_plates = conn.execute(
            "SELECT DISTINCT plate FROM shift_logs WHERE plate IS NOT NULL AND TRIM(plate) <> ''"
        ).fetchall()
        for (log_plate,) in existing_log_plates:
            conn.execute(
                "INSERT OR IGNORE INTO vehicle_plates (plate, active, notes) VALUES (?, 1, ?)",
                (normalize_plate(log_plate), "Eski vardiya loglarından otomatik aktarıldı"),
            )

        conn.executemany(
            "INSERT OR IGNORE INTO groups (name, description) VALUES (?, ?)",
            INITIAL_GROUPS,
        )

        seed_row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            ("driver_group_seed_version",),
        ).fetchone()
        seed_already_applied = bool(seed_row and seed_row[0] == SEED_VERSION)

        group_id_by_name = {
            row[0]: row[1]
            for row in conn.execute("SELECT name, id FROM groups").fetchall()
        }

        if not seed_already_applied:
            for old_name, new_name in LEGACY_DRIVER_NAME_ALIASES:
                old_clean = normalize_name(old_name)
                new_clean = normalize_name(new_name)
                old_row = conn.execute("SELECT id FROM drivers WHERE full_name = ?", (old_clean,)).fetchone()
                new_row = conn.execute("SELECT id FROM drivers WHERE full_name = ?", (new_clean,)).fetchone()
                if old_row and not new_row:
                    conn.execute(
                        "UPDATE drivers SET full_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (new_clean, old_row[0]),
                    )

            for driver_name, group_name in INITIAL_DRIVER_GROUP_ASSIGNMENTS:
                clean_name = normalize_name(driver_name)
                group_id = group_id_by_name[group_name]
                existing = conn.execute("SELECT id FROM drivers WHERE full_name = ?", (clean_name,)).fetchone()
                if existing:
                    conn.execute(
                        "UPDATE drivers SET group_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (group_id, existing[0]),
                    )
                else:
                    conn.execute(
                        "INSERT INTO drivers (full_name, group_id, active) VALUES (?, ?, 1)",
                        (clean_name, group_id),
                    )

            official_group_names = {name for name, _desc in INITIAL_GROUPS}
            for legacy_group_name in LEGACY_GROUP_NAMES:
                if legacy_group_name in official_group_names:
                    continue
                row = conn.execute("SELECT id FROM groups WHERE name = ?", (legacy_group_name,)).fetchone()
                if not row:
                    continue
                usage = conn.execute("SELECT COUNT(*) FROM drivers WHERE group_id = ?", (row[0],)).fetchone()[0]
                if usage == 0:
                    conn.execute("DELETE FROM groups WHERE id = ?", (row[0],))

            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                ("driver_group_seed_version", SEED_VERSION),
            )
        conn.commit()


def ensure_runtime_config() -> bool:
    """Eksik Supabase/şifre ayarlarını kullanıcıya anlaşılır şekilde gösterir."""
    missing = []
    if not get_database_url():
        missing.append("DATABASE_URL")
    if not get_config_value("MANAGER_PASSWORD"):
        missing.append("MANAGER_PASSWORD")
    if not get_config_value("COORDINATOR_PASSWORD"):
        missing.append("COORDINATOR_PASSWORD")

    if not missing:
        return True

    inject_css("Açık")
    render_header(
        "Kurulum Ayarları Eksik",
        "Supabase PostgreSQL bağlantısı ve giriş şifreleri Streamlit Secrets içine eklenmeli.",
    )
    st.error("Eksik ayarlar: " + ", ".join(missing))
    st.markdown("Streamlit Cloud > App > Settings > Secrets bölümüne şu formatta ekle:")
    st.code('DATABASE_URL = "postgresql://..."\nMANAGER_PASSWORD = "müdür_şifren"\nCOORDINATOR_PASSWORD = "koordine_şifren"', language="toml")
    st.info("Bu bilgiler GitHub koduna yazılmaz. Böylece uygulama reboot olsa bile veriler Supabase PostgreSQL içinde kalır.")
    return False


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
            .hero-plane {{
                width: 84px;
                height: 84px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 24px;
                background: linear-gradient(135deg, var(--c-surface2), var(--c-surface));
                border: 1px solid var(--c-border);
                box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 14px 24px rgba(0,0,0,.10);
                font-size: 40px;
                animation: heroPlaneFloat 3.2s ease-in-out infinite;
            }}
            @keyframes heroPlaneFloat {{
                0%, 100% {{ transform: translateY(0) rotate(-6deg); }}
                50% {{ transform: translateY(-7px) rotate(2deg); }}
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


            /* OKUNABİLİRLİK DÜZELTMESİ
               Streamlit bazı widget yazılarını tema geçişlerinde beyaz bırakabiliyor.
               Aşağıdaki kurallar tüm label, input, dropdown, sidebar, tab ve tablo başlıklarını
               seçilen temaya göre okunur hale getirir. */
            .stApp, .stApp * {{
                color: var(--c-text);
            }}
            [data-testid="stSidebar"], [data-testid="stSidebar"] * {{
                color: var(--c-text) !important;
            }}
            [data-testid="stMarkdownContainer"],
            [data-testid="stMarkdownContainer"] *,
            [data-testid="stWidgetLabel"],
            [data-testid="stWidgetLabel"] *,
            [data-testid="stCaptionContainer"],
            [data-testid="stCaptionContainer"] *,
            label, label *,
            p, span, small, strong, em,
            h1, h2, h3, h4, h5, h6 {{
                color: var(--c-text) !important;
            }}
            [data-testid="stCaptionContainer"],
            .soft-note,
            .hero-subtitle {{
                color: var(--c-muted) !important;
            }}
            input, textarea,
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            .stDateInput input {{
                color: var(--c-text) !important;
                background-color: var(--c-surface) !important;
                border-color: var(--c-border) !important;
                caret-color: var(--c-text) !important;
            }}
            input::placeholder, textarea::placeholder {{
                color: var(--c-muted) !important;
                opacity: 1 !important;
            }}
            div[data-baseweb="select"] > div,
            div[data-baseweb="select"] span,
            div[data-baseweb="select"] input,
            div[data-baseweb="select"] svg {{
                color: var(--c-text) !important;
                fill: var(--c-text) !important;
            }}
            div[data-baseweb="select"] > div {{
                background-color: var(--c-surface) !important;
                border-color: var(--c-border) !important;
            }}
            div[data-baseweb="popover"],
            div[data-baseweb="popover"] *,
            ul[role="listbox"],
            ul[role="listbox"] *,
            div[role="listbox"],
            div[role="listbox"] *,
            div[role="option"],
            div[role="option"] * {{
                color: var(--c-text) !important;
                background-color: var(--c-surface) !important;
            }}
            div[role="option"]:hover,
            div[role="option"][aria-selected="true"] {{
                background-color: var(--c-surface2) !important;
            }}
            button,
            button *,
            .stButton button,
            .stButton button *,
            .stDownloadButton button,
            .stDownloadButton button * {{
                color: var(--c-text) !important;
            }}
            .stButton>button[kind="primary"],
            .stButton>button[kind="primary"] *,
            .stFormSubmitButton>button[kind="primary"],
            .stFormSubmitButton>button[kind="primary"] * {{
                color: {primary_button_text} !important;
            }}
            button[data-baseweb="tab"],
            button[data-baseweb="tab"] * {{
                color: var(--c-text) !important;
            }}
            [data-testid="stMetric"],
            [data-testid="stMetric"] *,
            [data-testid="stMetricLabel"],
            [data-testid="stMetricValue"],
            [data-testid="stMetricDelta"] {{
                color: var(--c-text) !important;
            }}
            [data-testid="stExpander"],
            [data-testid="stExpander"] * {{
                color: var(--c-text) !important;
            }}
            [data-testid="stDataFrame"] *,
            [data-testid="stTable"] * {{
                color: var(--c-text) !important;
            }}
            .stAlert, .stAlert * {{
                color: var(--c-text) !important;
            }}

            @media (max-width: 780px) {{
                .hero-card {{
                    flex-direction: column;
                    align-items: flex-start;
                    padding: 18px;
                }}
                .hero-left {{ flex-direction: column; align-items: flex-start; }}
                .hero-title {{ font-size: 22px; }}
                .hero-plane {{ width: 70px; height: 70px; font-size: 34px; }}
                .pill {{ white-space: normal; }}
                .block-container {{ padding-left: 0.9rem; padding-right: 0.9rem; }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-left">
                <div class="hero-plane">✈️</div>
                <div>
                    <div class="hero-title">{title}</div>
                    <p class="hero-subtitle">{subtitle}</p>
                </div>
            </div>
            <div class="pill">Supabase PostgreSQL · Streamlit panel · Mobil uyumlu</div>
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
        SELECT d.id, d.full_name, d.group_id, g.name AS group_name, d.active
        FROM drivers d
        LEFT JOIN groups g ON g.id = d.group_id
        {where}
        ORDER BY d.full_name
        """
    )
    return df.to_dict("records")


def get_vehicle_df(include_inactive: bool = True) -> pd.DataFrame:
    where = "" if include_inactive else "WHERE v.active = 1"
    return read_df(
        f"""
        SELECT
            v.id,
            v.plate AS 'Plaka',
            CASE WHEN v.active = 1 THEN 'Aktif' ELSE 'Pasif' END AS 'Durum',
            COALESCE(logs.log_count, 0) AS 'Log Sayısı',
            v.notes AS 'Not',
            v.created_at AS 'Eklenme Zamanı',
            v.updated_at AS 'Güncelleme Zamanı'
        FROM vehicle_plates v
        LEFT JOIN (
            SELECT plate, COUNT(*) AS log_count
            FROM shift_logs
            GROUP BY plate
        ) logs ON logs.plate = v.plate
        {where}
        ORDER BY v.active DESC, v.plate ASC
        """
    )


def get_plate_options(include_inactive: bool = True, include_log_values: bool = True) -> list[str]:
    vehicle_where = "" if include_inactive else "WHERE active = 1"
    if include_log_values:
        query = f"""
        SELECT plate FROM vehicle_plates {vehicle_where}
        UNION
        SELECT DISTINCT plate
        FROM shift_logs
        WHERE plate IS NOT NULL AND TRIM(plate) <> ''
        ORDER BY plate
        """
    else:
        query = f"""
        SELECT plate
        FROM vehicle_plates
        {vehicle_where}
        ORDER BY plate
        """
    df = read_df(query)
    if df.empty:
        return []
    return [str(p) for p in df["plate"].dropna().tolist()]


def upsert_vehicle_plate(plate: str, note: str = "") -> None:
    clean_plate = normalize_plate(plate)
    if not clean_plate:
        return
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO vehicle_plates (plate, active, notes)
            VALUES (?, 1, ?)
            ON CONFLICT(plate) DO UPDATE SET active = 1, updated_at = CURRENT_TIMESTAMP
            """,
            (clean_plate, note.strip()),
        )
        conn.commit()


def get_shift_logs(
    start: Optional[date] = None,
    end: Optional[date] = None,
    driver_id: Optional[int] = None,
    group_id: Optional[int] = None,
    shift: Optional[str] = None,
    plate_exact: Optional[str] = None,
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
    if plate_exact and plate_exact != "Tümü":
        clauses.append("l.plate = ?")
        params.append(normalize_plate(plate_exact))
    elif plate_contains.strip():
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
            l.vehicle_take_time AS 'Araç Alma Saati',
            l.vehicle_drop_time AS 'Araç Bırakma Saati',
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
    st.sidebar.markdown("### ✈️ Driver Panel")
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

    tab_list, tab_add, tab_edit, tab_quick_group, tab_groups = st.tabs(
        ["Liste", "Yeni Sürücü Ekle", "Düzenle / Pasif-Sil", "Hızlı Grup Değiştir", "Grup Yönetimi"]
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


    with tab_quick_group:
        st.subheader("Sonradan grubu değişen personel için hızlı alan")
        st.caption("Personelin adı değişmeden sadece bağlı olduğu sürücü grubunu buradan güncelleyebilirsin. Geçmiş loglar bozulmaz; sadece personelin güncel grubu değişir.")

        options = get_driver_options(active_only=False)
        if not options:
            st.info("Henüz sürücü yok.")
        else:
            label_map = {
                f"{row['full_name']} · Mevcut grup: {row['group_name']} · {'Aktif' if row['active'] else 'Pasif'}": row
                for row in options
            }
            selected_quick_label = st.selectbox("Grubu değişecek sürücü", list(label_map.keys()), key="quick_group_driver")
            selected_quick = label_map[selected_quick_label]
            group_names_only = groups["name"].tolist()
            current_group_name = selected_quick.get("group_name") or group_names_only[0]
            current_index = group_names_only.index(current_group_name) if current_group_name in group_names_only else 0

            q1, q2 = st.columns([1, 1])
            q1.text_input("Mevcut grup", value=current_group_name, disabled=True)
            new_quick_group = q2.selectbox(
                "Yeni grup",
                group_names_only,
                index=current_index,
                key="quick_new_group",
            )
            change_note = st.text_input(
                "Değişiklik notu (opsiyonel)",
                placeholder="Örn: Eğitim tamamlandı, A sınıfına geçti",
                key="quick_group_note",
            )

            if st.button("Seçili sürücünün grubunu güncelle", type="primary", use_container_width=True):
                new_group_id = int(groups.loc[groups["name"] == new_quick_group, "id"].iloc[0])
                if new_quick_group == current_group_name:
                    st.info("Seçilen sürücü zaten bu grupta.")
                else:
                    if change_note.strip():
                        note_text = f"Grup değişikliği: {current_group_name} -> {new_quick_group}. {change_note.strip()}"
                        execute(
                            """
                            UPDATE drivers
                            SET group_id = ?,
                                notes = TRIM(COALESCE(NULLIF(notes, ''), '') || CASE WHEN COALESCE(NULLIF(notes, ''), '') = '' THEN '' ELSE ' | ' END || ?),
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (new_group_id, note_text, int(selected_quick["id"])),
                        )
                    else:
                        execute(
                            "UPDATE drivers SET group_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (new_group_id, int(selected_quick["id"])),
                        )
                    st.success(f"{selected_quick['full_name']} yeni gruba taşındı: {new_quick_group}")
                    st.rerun()

            st.markdown("---")
            st.subheader("Toplu grup değiştirme")
            st.caption("Aynı anda birden fazla sürücüyü aynı gruba almak için kullanılır.")
            bulk_group = st.selectbox("Toplu atanacak grup", group_names_only, key="bulk_group_target")
            bulk_labels = list(label_map.keys())
            selected_bulk_labels = st.multiselect("Sürücüleri seç", bulk_labels, key="bulk_group_drivers")
            if st.button("Seçili sürücüleri toplu güncelle", disabled=not selected_bulk_labels, use_container_width=True):
                bulk_group_id = int(groups.loc[groups["name"] == bulk_group, "id"].iloc[0])
                selected_ids = [int(label_map[label]["id"]) for label in selected_bulk_labels]
                executemany(
                    "UPDATE drivers SET group_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    [(bulk_group_id, driver_id) for driver_id in selected_ids],
                )
                st.success(f"{len(selected_ids)} sürücünün grubu {bulk_group} olarak güncellendi.")
                st.rerun()

    with tab_groups:
        st.subheader("10 Resmi Grup Tanımı")
        st.caption("Bu gruplar yüklediğin resmi sürücü/grup listesine göre başlangıçta otomatik tanımlanır. İsim/açıklama değişikliklerini buradan yapabilirsin.")
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


def page_vehicle_management() -> None:
    render_header(
        "Plaka Yönetimi",
        "Resmi araç plakalarını ekle, düzelt, pasife al veya hatalı girilen plakaları güvenli şekilde sil.",
    )

    vehicles = get_vehicle_df(include_inactive=True)
    tab_list, tab_add, tab_edit, tab_bulk = st.tabs(
        ["Liste", "Yeni Plaka Ekle", "Düzenle / Pasif-Sil", "Toplu Plaka Yükle"]
    )

    with tab_list:
        f1, f2 = st.columns([2, 1])
        search = f1.text_input("Plaka içinde ara", placeholder="Örn: TBTU0003", key="vehicle_search")
        status = f2.selectbox("Durum", ["Tümü", "Aktif", "Pasif"], key="vehicle_status_filter")
        filtered = vehicles.copy()
        if search.strip():
            filtered = filtered[filtered["Plaka"].astype(str).str.upper().str.contains(search.upper().strip(), na=False)]
        if status != "Tümü":
            filtered = filtered[filtered["Durum"] == status]

        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Plaka", len(vehicles))
        c2.metric("Aktif Plaka", int((vehicles["Durum"] == "Aktif").sum()) if not vehicles.empty else 0)
        c3.metric("Filtrelenen", len(filtered))

        st.dataframe(filtered, use_container_width=True, hide_index=True)
        if not filtered.empty:
            show_downloads(filtered, "plaka_listesi")

    with tab_add:
        st.subheader("Yeni plaka ekle")
        with st.form("add_vehicle_form", clear_on_submit=True):
            new_plate = st.text_input("Plaka", placeholder="Örn: TBTU000999")
            new_note = st.text_area("Not (opsiyonel)", placeholder="Örn: Yeni araç, yedek araç")
            submitted = st.form_submit_button("Plakayı ekle", type="primary", use_container_width=True)

        if submitted:
            clean_plate = normalize_plate(new_plate)
            if not clean_plate:
                st.error("Plaka boş bırakılamaz.")
            elif fetch_one("SELECT id FROM vehicle_plates WHERE plate = ?", (clean_plate,)):
                st.warning("Bu plaka zaten kayıtlı.")
            else:
                execute(
                    "INSERT INTO vehicle_plates (plate, active, notes) VALUES (?, 1, ?)",
                    (clean_plate, new_note.strip()),
                )
                st.success(f"{clean_plate} plaka listesine eklendi.")
                st.rerun()

    with tab_edit:
        st.subheader("Plaka düzeltme / pasife alma / silme")
        raw_vehicles = read_df("SELECT id, plate, active, notes FROM vehicle_plates ORDER BY active DESC, plate ASC")
        if raw_vehicles.empty:
            st.info("Henüz kayıtlı plaka yok.")
        else:
            label_map = {
                f"{row['plate']} · {'Aktif' if int(row['active']) else 'Pasif'}": row
                for _, row in raw_vehicles.iterrows()
            }
            selected_label = st.selectbox("Düzenlenecek plaka", list(label_map.keys()), key="vehicle_edit_select")
            selected = label_map[selected_label]
            old_plate = str(selected["plate"])
            log_count = int(fetch_one("SELECT COUNT(*) FROM shift_logs WHERE plate = ?", (old_plate,))[0])
            st.caption(f"Bu plakaya bağlı geçmiş log sayısı: {log_count}")

            with st.form("edit_vehicle_form"):
                c1, c2 = st.columns(2)
                edited_plate = c1.text_input("Plaka", value=old_plate)
                edited_status = c2.selectbox("Durum", ["Aktif", "Pasif"], index=0 if int(selected["active"]) else 1)
                edited_note = st.text_area("Not", value=selected["notes"] or "")
                sync_logs = st.checkbox(
                    "Plaka adı değişirse geçmiş loglardaki eski plakayı da yeni plakaya çevir",
                    value=True,
                    help="Yanlış yazılmış plaka düzeltmelerinde bunu açık bırak. Böylece filtrelerde eski hatalı plaka kalmaz.",
                )
                save_vehicle = st.form_submit_button("Plaka bilgisini güncelle", type="primary", use_container_width=True)

            if save_vehicle:
                clean_new_plate = normalize_plate(edited_plate)
                if not clean_new_plate:
                    st.error("Plaka boş bırakılamaz.")
                else:
                    duplicate = fetch_one(
                        "SELECT id FROM vehicle_plates WHERE plate = ? AND id <> ?",
                        (clean_new_plate, int(selected["id"])),
                    )
                    if duplicate:
                        st.error("Bu plaka başka bir kayıtta zaten var.")
                    else:
                        with connect() as conn:
                            conn.execute(
                                """
                                UPDATE vehicle_plates
                                SET plate = ?, active = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE id = ?
                                """,
                                (clean_new_plate, 1 if edited_status == "Aktif" else 0, edited_note.strip(), int(selected["id"])),
                            )
                            if sync_logs and clean_new_plate != old_plate:
                                conn.execute(
                                    "UPDATE shift_logs SET plate = ?, updated_at = CURRENT_TIMESTAMP WHERE plate = ?",
                                    (clean_new_plate, old_plate),
                                )
                            conn.commit()
                        st.success("Plaka bilgisi güncellendi.")
                        st.rerun()

            st.markdown("---")
            st.subheader("Kalıcı silme")
            st.caption("Geçmiş logu olan plaka kalıcı silinemez. Önce yukarıdan doğru plakaya çevir veya plakayı pasife al.")
            confirm_delete = st.checkbox("Bu plakayı kalıcı silmeyi onaylıyorum", key="confirm_vehicle_delete")
            if st.button("Seçili plakayı kalıcı sil", disabled=(not confirm_delete or log_count > 0), use_container_width=True):
                execute("DELETE FROM vehicle_plates WHERE id = ?", (int(selected["id"]),))
                st.success("Plaka kalıcı olarak silindi.")
                st.rerun()
            if log_count > 0:
                st.info("Bu plakaya bağlı geçmiş kayıt var. Kayıt geçmişini bozmamak için silme yerine düzeltme veya pasife alma kullan.")

    with tab_bulk:
        st.subheader("Toplu plaka yükle")
        st.caption("Her satıra bir plaka yazabilir veya virgülle ayırabilirsin. Var olan plakalar tekrar eklenmez.")
        sample_text = "\n".join(INITIAL_VEHICLE_PLATES[:8])
        bulk_text = st.text_area("Plaka listesi", value="", placeholder=sample_text, height=220)
        bulk_note = st.text_input("Toplu yükleme notu", value="Manuel toplu yükleme")
        if st.button("Toplu plakaları ekle", type="primary", use_container_width=True):
            raw_items = []
            for chunk in bulk_text.replace(",", "\n").splitlines():
                clean = normalize_plate(chunk)
                if clean:
                    raw_items.append(clean)
            unique_items = sorted(set(raw_items))
            if not unique_items:
                st.warning("Eklenecek plaka bulunamadı.")
            else:
                before = int(fetch_one("SELECT COUNT(*) FROM vehicle_plates")[0])
                executemany(
                    "INSERT OR IGNORE INTO vehicle_plates (plate, active, notes) VALUES (?, 1, ?)",
                    [(plate, bulk_note.strip()) for plate in unique_items],
                )
                after = int(fetch_one("SELECT COUNT(*) FROM vehicle_plates")[0])
                st.success(f"{after - before} yeni plaka eklendi. Zaten kayıtlı/tekrar olan: {len(unique_items) - (after - before)}")
                st.rerun()


def page_shift_entry() -> None:
    render_header(
        "Canlı Vardiya ve Araç Girişi",
        "Amirler günlük operasyon için sürücü, giriş-çıkış saati ve plaka eşleşmesini buradan işler.",
    )

    drivers = get_driver_options(active_only=True)
    if not drivers:
        st.warning("Aktif sürücü bulunamadı. Önce Sürücü Yönetimi sayfasından sürücü ekleyin veya aktife alın.")
        return

    st.markdown("### Tekil kayıt girişi")
    st.caption("Vardiya artık iki ayrı alanla girilir: giriş saati ve çıkış saati. Saat seçenekleri 5 dakika aralıklıdır.")
    with st.form("single_log_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        log_date = c1.date_input("Tarih", value=date.today(), format="DD.MM.YYYY")
        entry_time = c2.selectbox("Giriş Saati", TIME_OPTIONS, index=safe_time_index("08:00"))
        exit_time = c3.selectbox("Çıkış Saati", TIME_OPTIONS, index=safe_time_index("16:00"))

        driver_labels = [f"{d['full_name']} · {d['group_name']}" for d in drivers]
        driver_lookup = {f"{d['full_name']} · {d['group_name']}": d for d in drivers}
        selected_driver_label = c4.selectbox("Sürücü seçimi", driver_labels)

        c_vehicle_take, c_vehicle_drop = st.columns(2)
        vehicle_take_time = c_vehicle_take.selectbox("Araç Alma Saati", TIME_OPTIONS, index=safe_time_index(entry_time))
        vehicle_drop_time = c_vehicle_drop.selectbox("Araç Bırakma Saati", TIME_OPTIONS, index=safe_time_index(exit_time, "16:00"))

        c5, c6 = st.columns([1, 2])
        active_plate_options = get_plate_options(include_inactive=False, include_log_values=False)
        manual_choice = "Listede yok / manuel gir"
        plate_choice = c5.selectbox("Araç plakası", [""] + active_plate_options + [manual_choice])
        manual_plate = ""
        add_manual_to_master = False
        if plate_choice == manual_choice:
            manual_plate = c5.text_input("Manuel plaka", placeholder="Örn: TBTU000999")
            add_manual_to_master = c5.checkbox("Bu plakayı plaka listesine de ekle", value=True)
        plate = manual_plate if plate_choice == manual_choice else plate_choice
        note = c6.text_input("Not (opsiyonel)", placeholder="Örn: VIP görev, bagaj transferi")
        submitted = st.form_submit_button("Vardiya kaydını ekle", type="primary", use_container_width=True)

    if submitted:
        selected_driver = driver_lookup[selected_driver_label]
        clean_plate = normalize_plate(plate)
        clean_shift = make_shift_label(entry_time, exit_time)
        if not clean_plate:
            st.error("Araç plakası boş bırakılamaz.")
        else:
            if plate_choice == manual_choice and add_manual_to_master:
                upsert_vehicle_plate(clean_plate, "Vardiya girişinden otomatik eklendi")
            execute(
                "INSERT INTO shift_logs (log_date, driver_id, shift, plate, vehicle_take_time, vehicle_drop_time, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (log_date.isoformat(), int(selected_driver["id"]), clean_shift, clean_plate, vehicle_take_time, vehicle_drop_time, note.strip()),
            )
            st.success("Vardiya ve araç kaydı eklendi.")
            st.rerun()

    st.markdown("---")
    st.markdown("### Toplu kayıt girişi")
    st.caption("Aynı tarih için birden fazla sürücü kaydını hızlı girmek için tabloyu doldur. Giriş ve çıkış saatleri 5 dakika aralıklı seçilir.")

    driver_name_options = [d["full_name"] for d in drivers]
    active_plate_options_for_batch = get_plate_options(include_inactive=False, include_log_values=False)
    batch_date = st.date_input("Toplu kayıt tarihi", value=date.today(), format="DD.MM.YYYY", key="batch_date")
    initial_batch = pd.DataFrame(
        [{"Sürücü": "", "Giriş Saati": "08:00", "Çıkış Saati": "16:00", "Araç Alma Saati": "08:00", "Araç Bırakma Saati": "16:00", "Araç Plakası": "", "Not": ""} for _ in range(5)]
    )
    edited = st.data_editor(
        initial_batch,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Sürücü": st.column_config.SelectboxColumn("Sürücü", options=[""] + driver_name_options, required=False),
            "Giriş Saati": st.column_config.SelectboxColumn("Giriş Saati", options=TIME_OPTIONS, required=False),
            "Çıkış Saati": st.column_config.SelectboxColumn("Çıkış Saati", options=TIME_OPTIONS, required=False),
            "Araç Alma Saati": st.column_config.SelectboxColumn("Araç Alma Saati", options=TIME_OPTIONS, required=False),
            "Araç Bırakma Saati": st.column_config.SelectboxColumn("Araç Bırakma Saati", options=TIME_OPTIONS, required=False),
            "Araç Plakası": st.column_config.SelectboxColumn(
                "Araç Plakası",
                options=[""] + active_plate_options_for_batch,
                required=False,
                help="Plaka listede yoksa Plaka Yönetimi sayfasından ekleyebilir veya tekil girişte manuel yazabilirsin.",
            ),
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
            entry = str(row.get("Giriş Saati", "")).strip()
            exit_ = str(row.get("Çıkış Saati", "")).strip()
            vehicle_take = str(row.get("Araç Alma Saati", "")).strip()
            vehicle_drop = str(row.get("Araç Bırakma Saati", "")).strip()
            pl = normalize_plate(row.get("Araç Plakası", ""))
            nt = str(row.get("Not", "")).strip()
            if not dname and not entry and not exit_ and not pl:
                continue
            if dname in driver_id_by_name and entry in TIME_OPTIONS and exit_ in TIME_OPTIONS and vehicle_take in TIME_OPTIONS and vehicle_drop in TIME_OPTIONS and pl:
                rows_to_insert.append((batch_date.isoformat(), driver_id_by_name[dname], make_shift_label(entry, exit_), pl, vehicle_take, vehicle_drop, nt))
            else:
                skipped += 1
        if rows_to_insert:
            # Toplu girişte seçilen plaka master listeden gelir. Yine de güvenlik için eksikse master listeye eklenir.
            for _date, _driver_id, _shift, inserted_plate, _vehicle_take, _vehicle_drop, _note in rows_to_insert:
                upsert_vehicle_plate(inserted_plate, "Toplu vardiya girişinden otomatik eklendi")
            executemany(
                "INSERT INTO shift_logs (log_date, driver_id, shift, plate, vehicle_take_time, vehicle_drop_time, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
    shift_options = ["Tümü"] + (all_shifts_df["shift"].tolist() if not all_shifts_df.empty else DEFAULT_SHIFTS)
    plate_options = ["Tümü"] + get_plate_options(include_inactive=True, include_log_values=True)

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
        plate_exact = c8.selectbox("Plaka", plate_options)

        c9, c10 = st.columns([1, 3])
        plate_filter = c9.text_input("Plaka içinde ara", placeholder="Örn: TBTU0003")
        c10.caption("Plaka filtresi, Plaka Yönetimi listesinden ve geçmiş loglarda kullanılan plakalardan otomatik oluşur. Net plaka için dropdown; parça arama için metin kutusunu kullanabilirsin.")

    if start_date > end_date and not all_time:
        st.error("Başlangıç tarihi bitiş tarihinden büyük olamaz.")
        return

    df = get_shift_logs(
        start=None if all_time else start_date,
        end=None if all_time else end_date,
        driver_id=driver_id,
        group_id=group_id,
        shift=shift_filter,
        plate_exact=plate_exact,
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
        st.subheader("Hatalı kayıt düzeltme / silme")
        st.caption("Yanlış sürücü seçimi, yanlış vardiya saati, yanlış tarih, yanlış plaka veya yanlış not girildiyse kaydı silmeden buradan düzeltebilirsin.")
        record_labels = [
            f"{int(row['Kayıt ID'])} · {row['Tarih']} · {row['Sürücü']} · {row['Vardiya']} · {row['Araç Plakası']}"
            for _, row in df.iterrows()
        ]

        tab_edit_log, tab_delete_log = st.tabs(["Kaydı Düzenle", "Kaydı Sil"])

        with tab_edit_log:
            selected_record_edit = st.selectbox("Düzenlenecek kayıt", record_labels, key="edit_log_select")
            selected_id_edit = int(selected_record_edit.split(" · ")[0])
            raw_log_df = read_df(
                """
                SELECT l.id, l.log_date, l.driver_id, l.shift, l.plate, l.vehicle_take_time, l.vehicle_drop_time, l.note,
                       d.full_name, g.name AS group_name
                FROM shift_logs l
                JOIN drivers d ON d.id = l.driver_id
                LEFT JOIN groups g ON g.id = d.group_id
                WHERE l.id = ?
                """,
                (selected_id_edit,),
            )
            if raw_log_df.empty:
                st.warning("Seçilen kayıt bulunamadı.")
            else:
                raw_log = raw_log_df.iloc[0]
                current_start, current_end = parse_shift_label(raw_log["shift"])
                driver_labels_all = [f"{d['full_name']} · {d['group_name']} · {'Aktif' if d['active'] else 'Pasif'}" for d in drivers]
                driver_id_lookup = {int(d["id"]): i for i, d in enumerate(drivers)}
                current_driver_index = driver_id_lookup.get(int(raw_log["driver_id"]), 0)

                current_plate = normalize_plate(raw_log["plate"])
                editable_plate_options = get_plate_options(include_inactive=False, include_log_values=True)
                if current_plate and current_plate not in editable_plate_options:
                    editable_plate_options.append(current_plate)
                    editable_plate_options = sorted(set(editable_plate_options))
                manual_choice = "Listede yok / manuel gir"
                plate_choice_options = editable_plate_options + [manual_choice]
                current_plate_index = plate_choice_options.index(current_plate) if current_plate in plate_choice_options else plate_choice_options.index(manual_choice)

                with st.form("edit_log_form"):
                    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                    try:
                        current_date = datetime.fromisoformat(str(raw_log["log_date"])).date()
                    except Exception:
                        current_date = date.today()
                    edited_date = c1.date_input("Tarih", value=current_date, format="DD.MM.YYYY", key="edit_log_date")
                    edited_start = c2.selectbox("Giriş Saati", TIME_OPTIONS, index=safe_time_index(current_start), key="edit_log_start")
                    edited_end = c3.selectbox("Çıkış Saati", TIME_OPTIONS, index=safe_time_index(current_end, "16:00"), key="edit_log_end")
                    edited_driver_label = c4.selectbox("Sürücü", driver_labels_all, index=current_driver_index, key="edit_log_driver")

                    c_vehicle_take, c_vehicle_drop = st.columns(2)
                    edited_vehicle_take = c_vehicle_take.selectbox("Araç Alma Saati", TIME_OPTIONS, index=safe_time_index(str(raw_log.get("vehicle_take_time", "") or edited_start), edited_start), key="edit_log_vehicle_take")
                    edited_vehicle_drop = c_vehicle_drop.selectbox("Araç Bırakma Saati", TIME_OPTIONS, index=safe_time_index(str(raw_log.get("vehicle_drop_time", "") or edited_end), edited_end), key="edit_log_vehicle_drop")

                    c5, c6 = st.columns([1, 2])
                    edited_plate_choice = c5.selectbox("Araç Plakası", plate_choice_options, index=current_plate_index, key="edit_log_plate_choice")
                    edited_manual_plate = ""
                    if edited_plate_choice == manual_choice:
                        edited_manual_plate = c5.text_input("Manuel plaka", value=current_plate, key="edit_log_manual_plate")
                    edited_note = c6.text_input("Not", value=str(raw_log["note"] or ""), key="edit_log_note")
                    add_plate_if_missing = st.checkbox("Plaka listesinde yoksa otomatik ekle", value=True, key="edit_log_add_plate")
                    save_edit = st.form_submit_button("Bu kaydı güncelle", type="primary", use_container_width=True)

                if save_edit:
                    edited_driver_id = int(drivers[driver_labels_all.index(edited_driver_label)]["id"])
                    final_plate = normalize_plate(edited_manual_plate if edited_plate_choice == manual_choice else edited_plate_choice)
                    final_shift = make_shift_label(edited_start, edited_end)
                    if not final_plate:
                        st.error("Plaka boş bırakılamaz.")
                    else:
                        if add_plate_if_missing:
                            upsert_vehicle_plate(final_plate, "Geçmiş log düzenlemesinden otomatik eklendi")
                        execute(
                            """
                            UPDATE shift_logs
                            SET log_date = ?, driver_id = ?, shift = ?, plate = ?, vehicle_take_time = ?, vehicle_drop_time = ?, note = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (edited_date.isoformat(), edited_driver_id, final_shift, final_plate, edited_vehicle_take, edited_vehicle_drop, edited_note.strip(), selected_id_edit),
                        )
                        st.success("Log kaydı güncellendi.")
                        st.rerun()

            st.info("Sürücünün ismi yanlış yazıldıysa: Sürücü Yönetimi > Düzenle / Pasif-Sil alanından isim düzeltilebilir. İsim değişince geçmiş loglar da otomatik yeni isimle görünür.")

        with tab_delete_log:
            st.caption("Sadece tamamen yanlış girilen log kayıtları için kullanılmalı. Düzeltilebilecek hatalarda önce Kaydı Düzenle sekmesini kullan.")
            selected_record_delete = st.selectbox("Silinecek kayıt", record_labels, key="delete_log_select")
            selected_id_delete = int(selected_record_delete.split(" · ")[0])
            confirm = st.checkbox("Bu log kaydını silmeyi onaylıyorum", key="delete_log_confirm")
            if st.button("Seçili log kaydını sil", disabled=not confirm, use_container_width=True):
                execute("DELETE FROM shift_logs WHERE id = ?", (selected_id_delete,))
                st.success("Log kaydı silindi.")
                st.rerun()


def page_reports() -> None:
    render_header(
        "Analiz ve Raporlama",
        "Tarih aralığına göre rapor al; isme veya plakaya göre arama yaparak kimin hangi aracı kullandığını detaylı incele.",
    )

    drivers = get_driver_options(active_only=False)
    all_shifts_df = read_df("SELECT DISTINCT shift FROM shift_logs ORDER BY shift")
    shift_options = ["Tümü"] + (all_shifts_df["shift"].tolist() if not all_shifts_df.empty else DEFAULT_SHIFTS)
    plate_options = ["Tümü"] + get_plate_options(include_inactive=True, include_log_values=True)

    with st.expander("Rapor filtreleri", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        start_date = c1.date_input("Rapor başlangıç", value=date.today() - timedelta(days=30), format="DD.MM.YYYY", key="report_start")
        end_date = c2.date_input("Rapor bitiş", value=date.today(), format="DD.MM.YYYY", key="report_end")
        all_time = c3.checkbox("Tüm zamanlar", value=False, key="report_all_time")
        include_passive = c4.checkbox("Pasif sürücüleri dahil et", value=True, key="report_include_passive")

        c5, c6, c7 = st.columns([1.3, 1.8, 1])
        driver_search = c5.text_input(
            "İsim içinde ara",
            placeholder="Örn: Umut, Mehmet, Yasin",
            key="report_driver_search",
        )
        driver_label_options = ["Tümü"] + [f"{d['full_name']} · {d['group_name']}" for d in drivers]
        driver_label = c6.selectbox("Net personel seç", driver_label_options, key="report_driver_exact")
        driver_id = None
        if driver_label != "Tümü":
            driver_id = int(drivers[driver_label_options.index(driver_label) - 1]["id"])
        shift_filter = c7.selectbox("Vardiya", shift_options, key="report_shift")

        c8, c9 = st.columns([1.4, 1.6])
        plate_exact = c8.selectbox("Net plaka seç", plate_options, key="report_plate_exact")
        plate_search = c9.text_input(
            "Plaka içinde ara",
            placeholder="Örn: TBTU0003, 900001",
            key="report_plate_search",
        )

        st.caption(
            "Örnek kullanım: Sadece plaka seçersen o plakayı belirtilen tarihlerde kimlerin kullandığını görürsün. "
            "Sadece isim seçersen belirtilen tarihlerde o personelin hangi plakalarla, hangi vardiyalarda çalıştığını görürsün."
        )

    if start_date > end_date and not all_time:
        st.error("Başlangıç tarihi bitiş tarihinden büyük olamaz.")
        return

    df = get_shift_logs(
        start=None if all_time else start_date,
        end=None if all_time else end_date,
        driver_id=driver_id,
        shift=shift_filter,
        plate_exact=plate_exact,
        plate_contains=plate_search,
        include_passive=include_passive,
    )

    if driver_search.strip() and not df.empty:
        token = normalize_name(driver_search)
        df = df[df["Sürücü"].astype(str).str.upper().str.contains(token, na=False, regex=False)]

    active_driver_filter = driver_id is not None or bool(driver_search.strip())
    active_plate_filter = (plate_exact != "Tümü") or bool(plate_search.strip())

    if df.empty:
        st.info("Seçilen tarih / isim / plaka filtresine uygun raporlanacak kayıt bulunamadı.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Kayıt", len(df))
    c2.metric("Aktif Gün", df["Tarih"].nunique())
    c3.metric("Sürücü", df["Sürücü"].nunique())
    c4.metric("Araç", df["Araç Plakası"].nunique())

    if active_plate_filter:
        st.markdown("### Plaka kullanım özeti")
        st.caption("Bu bölüm seçilen plakanın veya plaka aramasının belirtilen tarihlerde kimler tarafından kullanıldığını gösterir.")
        plate_summary = (
            df.groupby(["Araç Plakası", "Sürücü", "Grup"], dropna=False)
            .agg(
                Kullanım=("Kayıt ID", "count"),
                İlk_Tarih=("Tarih", "min"),
                Son_Tarih=("Tarih", "max"),
                Vardiyalar=("Vardiya", lambda values: ", ".join(sorted(set(map(str, values))))),
            )
            .reset_index()
            .sort_values(["Araç Plakası", "Kullanım", "Sürücü"], ascending=[True, False, True])
        )
        st.dataframe(plate_summary, use_container_width=True, hide_index=True)
        show_downloads(plate_summary, "plaka_kullanim_ozeti")

    if active_driver_filter:
        st.markdown("### Personel faaliyet özeti")
        st.caption("Bu bölüm seçilen ismin belirtilen tarihlerde hangi plakaları kullandığını ve hangi vardiyalarda görev aldığını gösterir.")

        tab_vehicle, tab_shift, tab_day = st.tabs(["Kullandığı plakalar", "Vardiya dağılımı", "Günlük detay"])
        with tab_vehicle:
            driver_vehicle_summary = (
                df.groupby(["Sürücü", "Araç Plakası"], dropna=False)
                .agg(
                    Kullanım=("Kayıt ID", "count"),
                    İlk_Tarih=("Tarih", "min"),
                    Son_Tarih=("Tarih", "max"),
                    Vardiyalar=("Vardiya", lambda values: ", ".join(sorted(set(map(str, values))))),
                )
                .reset_index()
                .sort_values(["Sürücü", "Kullanım", "Araç Plakası"], ascending=[True, False, True])
            )
            st.dataframe(driver_vehicle_summary, use_container_width=True, hide_index=True)
            show_downloads(driver_vehicle_summary, "personel_plaka_ozeti")

        with tab_shift:
            driver_shift_summary = (
                df.groupby(["Sürücü", "Vardiya"], dropna=False)
                .agg(
                    Kayıt=("Kayıt ID", "count"),
                    Araç_Sayısı=("Araç Plakası", "nunique"),
                    İlk_Tarih=("Tarih", "min"),
                    Son_Tarih=("Tarih", "max"),
                )
                .reset_index()
                .sort_values(["Sürücü", "Kayıt", "Vardiya"], ascending=[True, False, True])
            )
            st.dataframe(driver_shift_summary, use_container_width=True, hide_index=True)
            show_downloads(driver_shift_summary, "personel_vardiya_ozeti")

        with tab_day:
            daily_detail = df[["Tarih", "Sürücü", "Grup", "Vardiya", "Araç Alma Saati", "Araç Bırakma Saati", "Araç Plakası", "Not", "Kayıt ID"]].sort_values(
                ["Tarih", "Sürücü", "Vardiya"], ascending=[False, True, True]
            )
            st.dataframe(daily_detail, use_container_width=True, hide_index=True)

    daily = df.groupby("Tarih", as_index=False).size().rename(columns={"size": "Kayıt"})
    shift = df.groupby("Vardiya", as_index=False).size().rename(columns={"size": "Kayıt"}).sort_values("Kayıt", ascending=False)
    group = df.groupby("Grup", as_index=False).size().rename(columns={"size": "Kayıt"}).sort_values("Kayıt", ascending=False)
    vehicles = df.groupby("Araç Plakası", as_index=False).size().rename(columns={"size": "Kullanım"}).sort_values("Kullanım", ascending=False).head(15)
    drivers_top = df.groupby("Sürücü", as_index=False).size().rename(columns={"size": "Kayıt"}).sort_values("Kayıt", ascending=False).head(15)

    st.markdown("### Grafikler")
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
    st.dataframe(drivers_top, use_container_width=True, hide_index=True)

    st.markdown("### Filtrelenmiş rapor verisi")
    st.dataframe(df, use_container_width=True, hide_index=True)
    show_downloads(df, "analiz_raporu_filtreli")

def page_settings() -> None:
    render_header(
        "Ayarlar ve Yedekleme",
        "Supabase PostgreSQL bağlantısını, seed durumunu ve dışa aktarım yedeklerini kontrol et.",
    )

    st.markdown("### Sistem durumu")
    c1, c2, c3 = st.columns(3)
    c1.metric("Veritabanı", "Supabase PostgreSQL")
    c2.metric("Sürücü Seed", len(INITIAL_DRIVERS))
    c3.metric("Plaka Seed", len(INITIAL_VEHICLE_PLATES))

    st.code(f"DATABASE_URL: {mask_database_url(get_database_url())}")

    st.markdown("### Yedek indir")
    st.caption("Bu bölüm veritabanı dosyası indirmez; Supabase'deki canlı verileri CSV / Excel / PDF olarak dışa aktarır.")
    all_logs = get_shift_logs(start=None, end=None, include_passive=True)
    if all_logs.empty:
        st.info("Henüz indirilecek vardiya logu yok.")
    else:
        show_downloads(all_logs, "tum_vardiya_loglari_yedek")

    st.markdown("### Kurulum notu")
    st.markdown(
        """
        - Veriler artık Streamlit içine değil, Supabase PostgreSQL veritabanına kaydedilir.
        - Uygulama reboot olsa veya yeniden deploy edilse bile kayıtlar Supabase tarafında kalır.
        - GitHub koduna şifre veya veritabanı bağlantısı yazma; bunları Streamlit Secrets içinde tut.
        - Ek güvenlik için düzenli olarak bu sayfadan Excel yedeği indir.
        """
    )

    with st.expander("Tehlikeli alan: Canlı veritabanını sıfırla"):
        st.warning("Bu işlem Supabase PostgreSQL içindeki tüm vardiya loglarını, sürücüleri, plakaları ve ayarları siler. Sadece test kurulumunda kullan.")
        confirm_text = st.text_input("Sıfırlamak için SUPABASE SIFIRLA yaz")
        if st.button("Canlı veritabanını sıfırla", disabled=confirm_text != "SUPABASE SIFIRLA", use_container_width=True):
            with connect() as conn:
                conn.execute("TRUNCATE TABLE shift_logs, drivers, groups, vehicle_plates, app_settings RESTART IDENTITY CASCADE")
                conn.commit()
            init_db()
            st.success("Supabase veritabanı sıfırlandı ve başlangıç verileri yeniden yüklendi.")
            st.rerun()


# -----------------------------
# Giriş / Yetkilendirme
# -----------------------------
def hide_sidebar_for_login() -> None:
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
            .block-container { padding-top: 0 !important; max-width: 100% !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_login_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at 18% 20%, rgba(255,255,255,.24) 0, rgba(255,255,255,0) 24%),
                    radial-gradient(circle at 82% 18%, rgba(255,255,255,.18) 0, rgba(255,255,255,0) 24%),
                    linear-gradient(135deg, #06101f 0%, #0d2444 42%, #111827 100%);
                overflow-x: hidden;
            }
            .login-shell {
                min-height: 100vh;
                position: relative;
                padding: 48px 6vw 42px 6vw;
                color: #ffffff;
            }
            .login-grid {
                position: relative;
                z-index: 5;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 26px;
                align-items: stretch;
                max-width: 1180px;
                margin: 0 auto;
                padding-top: 44px;
            }
            .login-title-card {
                position: relative;
                z-index: 5;
                max-width: 1180px;
                margin: 0 auto;
                border: 1px solid rgba(255,255,255,.18);
                background: rgba(255,255,255,.10);
                backdrop-filter: blur(18px);
                border-radius: 30px;
                padding: 30px 34px;
                box-shadow: 0 28px 90px rgba(0,0,0,.32);
                overflow: hidden;
            }
            .login-kicker {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 13px;
                border: 1px solid rgba(255,255,255,.20);
                border-radius: 999px;
                color: rgba(255,255,255,.86);
                background: rgba(255,255,255,.08);
                font-size: 13px;
                margin-bottom: 14px;
            }
            .login-title {
                font-size: clamp(34px, 4vw, 58px);
                line-height: 1.02;
                letter-spacing: -0.05em;
                font-weight: 900;
                margin: 0 0 12px 0;
                color: #ffffff;
            }
            .login-subtitle {
                font-size: 16px;
                line-height: 1.65;
                max-width: 720px;
                color: rgba(255,255,255,.74);
                margin: 0;
            }
            .login-card {
                border: 1px solid rgba(255,255,255,.16);
                background: rgba(255,255,255,.11);
                backdrop-filter: blur(18px);
                border-radius: 28px;
                padding: 26px;
                box-shadow: 0 24px 75px rgba(0,0,0,.28);
                min-height: 270px;
                transition: transform .25s ease, border-color .25s ease, background .25s ease;
            }
            .login-card:hover {
                transform: translateY(-5px);
                border-color: rgba(255,255,255,.34);
                background: rgba(255,255,255,.15);
            }
            .login-card h3 {
                color: #ffffff !important;
                font-size: 27px;
                margin: 0 0 10px 0;
                letter-spacing: -0.02em;
            }
            .login-card p, .login-card li {
                color: rgba(255,255,255,.76) !important;
                font-size: 14px;
                line-height: 1.55;
            }
            .role-chip {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 8px 12px;
                border-radius: 999px;
                border: 1px solid rgba(255,255,255,.18);
                color: rgba(255,255,255,.86);
                background: rgba(255,255,255,.08);
                font-size: 13px;
                margin-bottom: 16px;
            }
            .login-form-wrap {
                position: relative;
                z-index: 8;
                max-width: 520px;
                margin: 28px auto 0 auto;
                border: 1px solid rgba(255,255,255,.18);
                background: rgba(255,255,255,.12);
                backdrop-filter: blur(18px);
                border-radius: 26px;
                padding: 22px 24px;
                box-shadow: 0 22px 68px rgba(0,0,0,.30);
            }
            .login-form-title {
                color: #ffffff;
                font-weight: 800;
                font-size: 22px;
                margin-bottom: 4px;
            }
            .login-form-subtitle {
                color: rgba(255,255,255,.70);
                font-size: 13px;
                margin-bottom: 14px;
            }
            .plane-stage {
                position: absolute;
                inset: 0;
                pointer-events: none;
                overflow: hidden;
                z-index: 1;
            }
            .plane {
                position: absolute;
                top: 18%;
                left: -14%;
                font-size: 68px;
                filter: drop-shadow(0 16px 20px rgba(0,0,0,.35));
                animation: flyAcross 9s cubic-bezier(.45,.05,.25,1) infinite;
            }
            .plane::after {
                content: "";
                position: absolute;
                width: 180px;
                height: 2px;
                right: 54px;
                top: 46px;
                background: linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,.45));
                transform: rotate(-8deg);
            }
            .cloud {
                position: absolute;
                width: 240px;
                height: 70px;
                border-radius: 999px;
                background: rgba(255,255,255,.08);
                filter: blur(.2px);
                animation: cloudMove 18s linear infinite;
            }
            .cloud.one { top: 24%; left: 8%; animation-delay: -2s; }
            .cloud.two { top: 58%; left: 62%; width: 310px; opacity: .76; animation-delay: -8s; }
            .cloud.three { top: 78%; left: 16%; width: 190px; opacity: .54; animation-delay: -12s; }
            @keyframes flyAcross {
                0% { transform: translate3d(0, 38px, 0) rotate(-8deg); opacity: 0; }
                9% { opacity: 1; }
                50% { transform: translate3d(56vw, -28px, 0) rotate(5deg); opacity: 1; }
                88% { opacity: 1; }
                100% { transform: translate3d(122vw, -88px, 0) rotate(7deg); opacity: 0; }
            }
            @keyframes cloudMove {
                0% { transform: translateX(-18vw); }
                100% { transform: translateX(112vw); }
            }
            .login-shell .stButton > button {
                width: 100%;
                border-radius: 16px;
                height: 52px;
                border: 1px solid rgba(255,255,255,.22);
                background: rgba(255,255,255,.94);
                color: #0b1220 !important;
                font-weight: 800;
                box-shadow: 0 14px 36px rgba(0,0,0,.22);
                transition: transform .2s ease, box-shadow .2s ease;
            }
            .login-shell .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 18px 44px rgba(0,0,0,.32);
                border-color: rgba(255,255,255,.55);
            }
            .login-shell input {
                color: #ffffff !important;
                background: rgba(255,255,255,.10) !important;
                border: 1px solid rgba(255,255,255,.22) !important;
                border-radius: 14px !important;
            }
            .login-shell label, .login-shell label * {
                color: rgba(255,255,255,.82) !important;
            }
            .login-shell .stAlert, .login-shell .stAlert * {
                color: #ffffff !important;
            }
            @media (max-width: 820px) {
                .login-shell { padding: 24px 16px; }
                .login-grid { grid-template-columns: 1fr; padding-top: 18px; }
                .login-title-card { padding: 24px; border-radius: 24px; }
                .login-card { min-height: auto; }
                .plane { font-size: 52px; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_login_page() -> bool:
    hide_sidebar_for_login()
    inject_login_css()

    if "auth_role" not in st.session_state:
        st.session_state.auth_role = None
    if "login_role_choice" not in st.session_state:
        st.session_state.login_role_choice = None

    st.markdown(
        """
        <div class="login-shell">
            <div class="plane-stage">
                <div class="plane">✈️</div>
                <div class="cloud one"></div>
                <div class="cloud two"></div>
                <div class="cloud three"></div>
            </div>
            <div class="login-title-card">
                <div class="login-kicker">✈️ Operasyon Paneli · Güvenli Giriş</div>
                <h1 class="login-title">Sürücü Vardiya ve Araç Yönetim Paneli</h1>
                <p class="login-subtitle">Devam etmek için yetki türünü seç. Müdür girişi tüm sayfalara erişir; koordine girişi günlük operasyon sayfalarına erişir.</p>
            </div>
            <div class="login-grid">
                <div class="login-card">
                    <div class="role-chip">👔 Sol taraf · Müdür</div>
                    <h3>Müdür Girişi</h3>
                    <p>Tüm yönetim ve raporlama alanlarına erişim sağlar.</p>
                    <ul>
                        <li>Geçmiş loglar</li>
                        <li>Analiz raporları</li>
                        <li>Ayarlar ve yedekleme</li>
                    </ul>
                </div>
                <div class="login-card">
                    <div class="role-chip">🧭 Sağ taraf · Koordine</div>
                    <h3>Koordine Girişi</h3>
                    <p>Günlük operasyon girişi ve temel yönetim alanlarına erişim sağlar.</p>
                    <ul>
                        <li>Ana sayfa</li>
                        <li>Sürücü ve plaka yönetimi</li>
                        <li>Vardiya girişi</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_left, c_right = st.columns(2)
    with c_left:
        if st.button("👔 Müdür Girişi", use_container_width=True):
            st.session_state.login_role_choice = "manager"
            st.rerun()
    with c_right:
        if st.button("🧭 Koordine Girişi", use_container_width=True):
            st.session_state.login_role_choice = "coordinator"
            st.rerun()

    selected_role = st.session_state.get("login_role_choice")
    if selected_role:
        role_label = "Müdür" if selected_role == "manager" else "Koordine"
        expected_password = get_config_value("MANAGER_PASSWORD") if selected_role == "manager" else get_config_value("COORDINATOR_PASSWORD")
        st.markdown(
            f"""
            <div class="login-form-wrap">
                <div class="login-form-title">{role_label} şifresi</div>
                <div class="login-form-subtitle">Seçilen giriş türü için şifreyi gir.</div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_password_form", clear_on_submit=False):
            password = st.text_input("Şifre", type="password")
            submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        if submitted:
            if password == expected_password:
                st.session_state.auth_role = selected_role
                st.session_state.auth_role_label = role_label
                st.session_state.login_role_choice = None
                st.rerun()
            else:
                st.error("Şifre hatalı. Lütfen tekrar dene.")

    return False


def is_logged_in() -> bool:
    return st.session_state.get("auth_role") in {"manager", "coordinator"}


def logout() -> None:
    for key in ["auth_role", "auth_role_label", "login_role_choice"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


# -----------------------------
# Uygulama ana akışı
# -----------------------------
def main() -> None:
    if not ensure_runtime_config():
        return
    init_db()

    if not is_logged_in():
        render_login_page()
        return

    sidebar_logo()
    theme = st.sidebar.selectbox("Tema", ["Açık", "Koyu"], index=0)
    inject_css(theme)

    role = st.session_state.get("auth_role", "coordinator")
    role_label = st.session_state.get("auth_role_label", "Koordine")
    allowed_pages = MANAGER_PAGES if role == "manager" else COORDINATOR_PAGES

    st.sidebar.markdown(f"**Giriş türü:** {role_label}")
    if st.sidebar.button("Çıkış yap", use_container_width=True):
        logout()

    st.sidebar.markdown("### Menü")
    page = st.sidebar.radio(
        "Sayfa seç",
        allowed_pages,
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Çelebi Hava Hizmetleri · Driver Shift Panel")

    if page == "Ana Sayfa":
        page_dashboard()
    elif page == "Sürücü Yönetimi":
        page_driver_management()
    elif page == "Plaka Yönetimi":
        page_vehicle_management()
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
