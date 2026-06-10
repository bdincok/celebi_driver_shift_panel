import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from panel.models import Driver, DriverGroup, Vehicle

OFFICIAL_DRIVER_GROUPS = ['A SINIFI',
 'C SINIFI',
 'D SINIFI',
 'KARGO TRAKTÖRÜ',
 'ŞUT TRAKTÖRÜ',
 'RAMP EMNİYET EKİBİ',
 'FOLLOW ME',
 'TEMIZLIK_TRAKTOR',
 'SINIF YÜKSELME EĞİTİMLERİ',
 'Tanımlanmamış / Diğer']

INITIAL_VEHICLE_PLATES = ['TBTU000074',
 'TBTU000078',
 'TBTU000080',
 'TBTU000094',
 'TBTU000141',
 'TBTU000142',
 'TBTU000143',
 'TBTU000146',
 'TBTU000147',
 'TBTU000149',
 'TBTU000150',
 'TBTU000154',
 'TBTU000155',
 'TBTU000156',
 'TBTU000259',
 'TBTU000260',
 'TBTU000276',
 'TBTU000293',
 'TBTU000294',
 'TBTU000295',
 'TBTU000296',
 'TBTU000297',
 'TBTU000299',
 'TBTU000300',
 'TBTU000301',
 'TBTU000303',
 'TBTU000304',
 'TBTU000305',
 'TBTU000306',
 'TBTU000308',
 'TBTU000309',
 'TBTU000310',
 'TBTU000311',
 'TBTU000312',
 'TBTU000313',
 'TBTU000314',
 'TBTU000315',
 'TBTU000316',
 'TBTU000317',
 'TBTU000320',
 'TBTU000321',
 'TBTU000323',
 'TBTU000331',
 'TBTU000332',
 'TBTU000333',
 'TBTU000334',
 'TBTU000363',
 'TBTU000364',
 'TBTU000365',
 'TBTU000366',
 'TBTU000371',
 'TBTU000381',
 'TBTU900001']

INITIAL_DRIVER_GROUP_ASSIGNMENTS = [('UMUT BOĞA', 'C SINIFI'),
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
 ('RAMAZAN BOZAN', 'C SINIFI')]


class Command(BaseCommand):
    help = 'Initial drivers, plates, groups and role users seed data.'

    def add_arguments(self, parser):
        parser.add_argument('--reset-passwords', action='store_true', help='Reset default role passwords from environment variables.')

    def handle(self, *args, **options):
        for name in OFFICIAL_DRIVER_GROUPS:
            DriverGroup.objects.get_or_create(name=name)

        default_group, _ = DriverGroup.objects.get_or_create(name='C SINIFI')
        for full_name, group_name in INITIAL_DRIVER_GROUP_ASSIGNMENTS:
            group, _ = DriverGroup.objects.get_or_create(name=group_name)
            driver, created = Driver.objects.get_or_create(
                full_name=full_name,
                defaults={'group': group, 'is_active': True},
            )
            if not created and driver.group_id != group.id:
                driver.group = group
                driver.save(update_fields=['group', 'updated_at'])

        for plate in INITIAL_VEHICLE_PLATES:
            Vehicle.objects.get_or_create(plate=plate, defaults={'is_active': True})

        self._ensure_roles(options['reset_passwords'])

        self.stdout.write(self.style.SUCCESS('Initial data loaded successfully.'))

    def _ensure_roles(self, reset_passwords):
        User = get_user_model()
        manager_group, _ = Group.objects.get_or_create(name='Müdür')
        coordinator_group, _ = Group.objects.get_or_create(name='Koordine')

        manager_password = os.getenv('MANAGER_PASSWORD', 'zaferberat32')
        coordinator_password = os.getenv('COORDINATOR_PASSWORD', 'ıstclb2026')

        manager, created = User.objects.get_or_create(username='mudur', defaults={'is_staff': True, 'is_superuser': True})
        manager.groups.add(manager_group)
        if created or reset_passwords:
            manager.set_password(manager_password)
            manager.is_staff = True
            manager.is_superuser = True
            manager.save()

        coordinator, created = User.objects.get_or_create(username='koordine', defaults={'is_staff': False, 'is_superuser': False})
        coordinator.groups.add(coordinator_group)
        if created or reset_passwords:
            coordinator.set_password(coordinator_password)
            coordinator.is_staff = False
            coordinator.is_superuser = False
            coordinator.save()
