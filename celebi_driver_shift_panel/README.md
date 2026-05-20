# Çelebi Sürücü Vardiya ve Araç Yönetim Paneli

Bu Streamlit uygulaması; sürücü yönetimi, günlük vardiya-plaka kaydı, geçmiş log filtreleme, Excel/CSV/PDF çıktı ve operasyon analizleri için hazırlanmıştır.

## Kurulum

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

- Repository: GitHub repo URL
- Branch: `main`
- Main file path: `app.py`

## Dosya Yapısı

```text
celebi_driver_shift_panel/
├── app.py
├── requirements.txt
├── README.md
├── assets/
│   └── celebi_logo.png
├── data/
│   └── celebi_driver_panel.sqlite3  # uygulama ilk çalışınca oluşur
└── .streamlit/
    └── config.toml
```

## Not

SQLite yerel/başlangıç aşaması için uygundur. Streamlit Cloud'da dosya sistemi kalıcılığı garanti edilmediği için gerçek operasyon kullanımında Supabase/PostgreSQL bağlantısı önerilir.
