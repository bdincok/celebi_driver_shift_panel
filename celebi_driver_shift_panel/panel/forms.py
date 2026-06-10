from datetime import date
from django import forms
from .models import Driver, DriverGroup, Vehicle, ShiftRecord

TIME_CHOICES = [('', 'Seçiniz')] + [
    (f'{hour:02d}:{minute:02d}', f'{hour:02d}:{minute:02d}')
    for hour in range(24)
    for minute in range(0, 60, 5)
]


class LoginPasswordForm(forms.Form):
    role = forms.ChoiceField(choices=[('mudur', 'Müdür'), ('koordine', 'Koordine')], widget=forms.HiddenInput)
    password = forms.CharField(label='Şifre', widget=forms.PasswordInput(attrs={'placeholder': 'Şifreyi girin'}))


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['full_name', 'group', 'is_active']
        labels = {
            'full_name': 'Ad Soyad',
            'group': 'Sınıf / Grup',
            'is_active': 'Aktif',
        }
        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Ad Soyad'}),
        }

    def clean_full_name(self):
        return ' '.join(self.cleaned_data['full_name'].upper().split())


class DriverGroupForm(forms.ModelForm):
    class Meta:
        model = DriverGroup
        fields = ['name']
        labels = {'name': 'Grup Adı'}

    def clean_name(self):
        return ' '.join(self.cleaned_data['name'].upper().split())


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate', 'is_active']
        labels = {'plate': 'Plaka', 'is_active': 'Aktif'}
        widgets = {'plate': forms.TextInput(attrs={'placeholder': 'Örn: TBTU000074'})}

    def clean_plate(self):
        return ''.join(self.cleaned_data['plate'].upper().split())


class ShiftRecordForm(forms.ModelForm):
    operation_date = forms.DateField(
        label='Tarih',
        initial=date.today,
        required=False,
        help_text='Boş bırakırsan otomatik olarak bugünün tarihi kaydedilir.',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    shift_start = forms.ChoiceField(label='Vardiya Giriş Saati', choices=TIME_CHOICES, initial='08:00')
    shift_end = forms.ChoiceField(label='Vardiya Çıkış Saati', choices=TIME_CHOICES, initial='16:00')
    vehicle_pickup_time = forms.ChoiceField(label='Araç Alma Saati', choices=TIME_CHOICES, required=False)
    vehicle_dropoff_time = forms.ChoiceField(label='Araç Bırakma Saati', choices=TIME_CHOICES, required=False)

    class Meta:
        model = ShiftRecord
        fields = [
            'operation_date',
            'driver',
            'shift_start',
            'shift_end',
            'vehicle_pickup_time',
            'vehicle_dropoff_time',
            'vehicle',
            'note',
        ]
        labels = {
            'driver': 'Sürücü',
            'vehicle': 'Plaka',
            'note': 'Not',
        }
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Opsiyonel not'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = Driver.objects.filter(is_active=True).select_related('group').order_by('full_name')
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True).order_by('plate')
        self.fields['vehicle'].required = True
        self.fields['driver'].empty_label = 'Sürücü seçiniz'
        self.fields['vehicle'].empty_label = 'Plaka seçiniz'
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()

    def clean_operation_date(self):
        return self.cleaned_data.get('operation_date') or date.today()


class ShiftFilterForm(forms.Form):
    start_date = forms.DateField(label='Başlangıç', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='Bitiş', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    driver = forms.ModelChoiceField(label='Sürücü', required=False, queryset=Driver.objects.none())
    vehicle = forms.ModelChoiceField(label='Plaka', required=False, queryset=Vehicle.objects.none())
    search = forms.CharField(label='İsim / Plaka Ara', required=False, widget=forms.TextInput(attrs={'placeholder': 'İsim veya plaka yaz'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['driver'].queryset = Driver.objects.all().order_by('full_name')
        self.fields['vehicle'].queryset = Vehicle.objects.all().order_by('plate')
        self.fields['driver'].empty_label = 'Tüm sürücüler'
        self.fields['vehicle'].empty_label = 'Tüm plakalar'
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
