# ISTCLB Driver Yerel Çift Tık Sürümü

Bu paket, Django tabanlı ISTCLB Driver panelinin yerel bilgisayarda çift tıklayarak çalıştırılabilen sürümüdür.

## Açılış

1. ZIP dosyasını çıkarın.
2. `BASLAT.bat` dosyasına çift tıklayın.
3. İlk kurulumdan sonra tarayıcıda `http://127.0.0.1:8000` açılır.

## Kullanıcılar

- Müdür şifresi: `zaferberat32`
- Koordine şifresi: `ıstclb2026`

## Veri Kaydı

Veriler şu dosyada tutulur:

```text
data/istclbdriver_local.sqlite3
```

Bu dosya ve `data` klasörü silinmediği sürece kayıtlar kalır.

## Yedekleme

- `BASLAT.bat` her açılışta otomatik yedek almaya çalışır.
- Manuel yedek için `YEDEK_AL.bat` kullanılabilir.
- Yedekler `backups` klasöründe saklanır.

## Not

Bu sürüm internette ortak kullanıma açık değildir. Yalnızca kurulduğu bilgisayarda çalışır.
Aynı anda farklı lokasyonlardan ortak veriyle kullanım için şirket ağı veya sunucu gerekir.
