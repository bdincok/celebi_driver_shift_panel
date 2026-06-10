# ISTCLBDRIVER - Streamlit + Supabase PostgreSQL

Bu sürüm GitHub + Streamlit Cloud üzerinde çalışmak ve verileri Supabase PostgreSQL içinde kalıcı tutmak için hazırlanmıştır.

## Streamlit Cloud ayarı

Main file path:

```text
app.py
```

## Secrets ayarı

Streamlit Cloud'da uygulamayı açtıktan sonra:

```text
Manage app > Settings > Secrets
```

şu değerleri ekle:

```toml
DATABASE_URL = "postgresql://kullanici:sifre@host:6543/postgres"
MANAGER_PASSWORD = "BURAYA_MUDUR_SIFRESI"
COORDINATOR_PASSWORD = "BURAYA_KOORDINE_SIFRESI"
```

> Şifreleri ve DATABASE_URL değerini GitHub koduna yazma. Sadece Streamlit Secrets içine koy.

## Supabase DATABASE_URL nereden alınır?

Supabase projesinde Database / Connect bölümünden PostgreSQL connection string alınır. Streamlit Cloud için genellikle SSL gerekli olduğu için kod otomatik `sslmode=require` ekler.

## Veri kalıcılığı

Bu sürümde Supabase PostgreSQL kullanılmaz. Veriler Supabase PostgreSQL tablolarına yazılır. Streamlit uygulaması reboot olsa veya yeniden deploy edilse bile veriler Supabase tarafında kalır.

## Özellikler

- Müdür / Koordine giriş sistemi
- Rol bazlı sayfa yetkileri
- Sürücü yönetimi
- Plaka yönetimi
- Tekli ve toplu vardiya girişi
- 5 dakika aralıklı saat seçenekleri
- Araç alma / araç bırakma saati
- Plaka zorunlu kayıt kuralı
- Geçmiş log düzenleme / silme
- Analiz grafikleri
- CSV / Excel / PDF indirme
