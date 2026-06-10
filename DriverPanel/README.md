# ISTCLBDRIVER Streamlit GitHub Sürümü

Bu klasör GitHub + Streamlit Cloud için hazırlanmıştır.

## GitHub'a yüklenecek dosyalar

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `README.md`

## Streamlit Cloud ayarı

Main file path:

```text
app.py
```

## Notlar

- Bu sürüm `psycopg`, `psycopg2` veya PostgreSQL paketi kullanmaz.
- Paket kurulumu için sadece `requirements.txt` içindeki Streamlit, pandas, plotly, reportlab ve openpyxl kurulur.
- Veri kaydı uygulama içindeki SQLite dosyasına yapılır.
- Streamlit Cloud üzerinde SQLite yerel dosya olduğu için platform yeniden deploy/reboot olduğunda kalıcılık garantisi yoktur.
