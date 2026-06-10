from django.urls import path
from . import views

urlpatterns = [
    path('', views.role_login, name='login'),
    path('giris/', views.role_login, name='role_login'),
    path('cikis/', views.logout_view, name='logout'),
    path('ana-sayfa/', views.dashboard, name='dashboard'),
    path('surucu-yonetimi/', views.driver_management, name='drivers'),
    path('surucu-yonetimi/<int:pk>/duzenle/', views.driver_edit, name='driver_edit'),
    path('surucu-yonetimi/<int:pk>/durum/', views.driver_toggle, name='driver_toggle'),
    path('plaka-yonetimi/', views.plate_management, name='plates'),
    path('plaka-yonetimi/<int:pk>/duzenle/', views.plate_edit, name='plate_edit'),
    path('plaka-yonetimi/<int:pk>/durum/', views.plate_toggle, name='plate_toggle'),
    path('vardiya-girisi/', views.shift_entry, name='shift_entry'),
    path('gecmis-loglar/', views.shift_logs, name='shift_logs'),
    path('gecmis-loglar/<int:pk>/duzenle/', views.shift_edit, name='shift_edit'),
    path('gecmis-loglar/<int:pk>/sil/', views.shift_delete, name='shift_delete'),
    path('analiz-raporlari/', views.analysis_reports, name='analysis'),
    path('export/vardiya-csv/', views.export_shift_csv, name='export_shift_csv'),
    path('export/vardiya-excel/', views.export_shift_excel, name='export_shift_excel'),
    path('export/vardiya-pdf/', views.export_shift_pdf, name='export_shift_pdf'),
]
