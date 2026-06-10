# Kurulum Hatası Düzeltmesi

Bu sürümde `psycopg2` kaldırıldı ve yerine Streamlit Cloud üzerinde daha sorunsuz kurulan `psycopg[binary]` kullanıldı.

GitHub repo kökünde şu dosyaların olduğundan emin ol:

- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`
- `.streamlit/secrets.toml.example`

Streamlit Cloud tarafında hata devam ederse:

1. GitHub'daki eski `packages.txt` dosyasını sil.
2. `requirements.txt` dosyasının yeni sürüm olduğunu kontrol et.
3. Streamlit Cloud > Manage app > Reboot app yap.
4. Hata devam ederse Manage app > Logs kısmında `ERROR:` yazan satırları kopyala.
