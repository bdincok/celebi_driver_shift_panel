# Çelebi Sürücü Vardiya ve Araç Yönetim Paneli

Bu Streamlit uygulaması sürücülerin vardiya, araç plakası ve grup bilgilerini manuel olarak yönetmek için hazırlanmıştır.

## Çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Repo kök dizinine bu klasörün içeriğini yüklersen:

```text
Main file path: app.py
```

Klasörü olduğu gibi repo içine koyarsan:

```text
Main file path: celebi_driver_shift_panel/app.py
```

## V7 güncellemesi

- Analiz Raporları ekranına isim arama filtresi eklendi.
- Analiz Raporları ekranına net plaka seçimi ve plaka içinde arama filtresi eklendi.
- Belirli tarih aralığında bir plakayı kimlerin kullandığı ayrı özet tabloda gösterilir.
- Belirli tarih aralığında bir personelin hangi plakaları kullandığı, vardiya dağılımı ve günlük detayları ayrı sekmelerde gösterilir.
- Tüm bu filtreli raporlar Excel, CSV ve PDF olarak indirilebilir.

## V6 güncellemesi

- Vardiya girişi artık tek metin alanı değildir; **Giriş Saati** ve **Çıkış Saati** ayrı seçilir.
- Giriş/çıkış saatleri 30 dakika aralıklı seçeneklerden gelir: 00:00, 00:30, 01:00 ... 23:30.
- Tekil ve toplu vardiya girişlerinde bu saat yapısı kullanılır.
- Geçmiş Loglar sayfasına **Kaydı Düzenle** sekmesi eklendi.
- Yanlış girilen tarih, sürücü, giriş saati, çıkış saati, plaka ve not silmeden düzeltilebilir.
- Tamamen hatalı kayıtlar için aynı alanda **Kaydı Sil** sekmesi korunur.
- Sürücü adı yanlışsa Sürücü Yönetimi > Düzenle / Pasif-Sil alanından isim düzeltilebilir; geçmiş loglar yeni isimle görünür.

## V5 güncellemesi

- 53 resmi TBTU plakası başlangıçta otomatik tanımlanır.
- Menüye **Plaka Yönetimi** sayfası eklendi.
- Plaka ekleme, toplu plaka yükleme, plaka düzeltme, pasife alma ve kalıcı silme alanları eklendi.
- Yanlış girilmiş plaka adı düzeltilirken geçmiş loglardaki eski plaka da yeni plakaya çevrilebilir.
- Geçmiş kaydı olan plakalar doğrudan silinmez; veri geçmişini bozmamak için önce düzeltme veya pasife alma yapılır.
- Vardiya girişinde araç plakası artık kayıtlı plaka listesinden seçilebilir; listede yoksa manuel giriş yapılabilir.
- Toplu vardiya girişinde yazılan yeni plakalar master plaka listesine otomatik eklenir ve sonra Plaka Yönetimi sayfasından düzeltilebilir.

## Önceki V4 güncellemesi

- 10 resmi sürücü grubu başlangıçta otomatik tanımlanır.
- 135 sürücü, yüklenen resmi listeye göre kendi grubuyla sisteme eklenir.
- Eski sürümden gelen veritabanlarında ilk açılışta resmi grup migration işlemi uygulanır.
- Sürücü Yönetimi > Hızlı Grup Değiştir alanından tekli veya toplu grup değişikliği yapılabilir.
- Geçmiş vardiya/plaka kayıtları korunur.
