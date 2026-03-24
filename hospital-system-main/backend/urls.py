"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from hospital import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.staff_login, name='staff_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Admin URLs - must come before django.contrib.admin.urls
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/staff/', views.staff_management, name='staff_management'),
    path('admin/staff/add/', views.add_staff, name='add_staff'),
    path('admin/staff/<int:user_id>/edit/', views.edit_staff, name='edit_staff'),
    path('admin/staff/<int:user_id>/delete/', views.delete_staff, name='delete_staff'),
    
    # Django admin URLs
    path('django-admin/', admin.site.urls),
    
    # Receptionist URLs
    path('receptionist/dashboard/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('receptionist/patients/', views.patient_list, name='patient_list'),
    path('receptionist/patients/add/', views.add_patient, name='add_patient'),
    path('receptionist/patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('receptionist/patients/<int:pk>/edit/', views.edit_patient, name='edit_patient'),
    path('receptionist/appointments/', views.appointment_list, name='appointment_list'),
    path('receptionist/appointments/add/', views.add_appointment, name='add_appointment'),
    
    # Doctor URLs
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/consultation/<int:appointment_id>/', views.consultation, name='consultation'),
    path('doctor/lab-tests/', views.lab_test_results, name='lab_test_results'),
    path('doctor/request-lab-test/', views.request_lab_test, name='request_lab_test'),
    path('doctor/prescribe-after-lab/<int:test_id>/', views.prescribe_after_lab, name='prescribe_after_lab'),
    path('doctor/patient-lab-queue/', views.patient_lab_queue, name='patient_lab_queue'),
    path('doctor/send-to-lab/<int:patient_id>/', views.send_to_lab, name='send_to_lab'),
    
    # Pharmacist URLs
    path('pharmacist/dashboard/', views.pharmacist_dashboard, name='pharmacist_dashboard'),
    path('pharmacist/prescribe/<int:prescription_id>/', views.prescribe_medicine, name='prescribe_medicine'),
    path('pharmacist/schedule/<int:prescription_id>/', views.schedule_prescription, name='schedule_prescription'),
    path('pharmacist/patient-history/', views.pharmacist_patient_history, name='pharmacist_patient_history'),
    path('pharmacist/patient-history/<int:patient_id>/', views.pharmacist_patient_detail, name='pharmacist_patient_detail'),
    
    # Lab Technician URLs
    path('lab-technician/dashboard/', views.lab_technician_dashboard, name='lab_technician_dashboard'),
    path('lab-technician/update-test/<int:test_id>/', views.update_lab_test, name='update_lab_test'),
    path('lab-technician/test-queue/', views.lab_test_queue, name='lab_test_queue'),
    path('lab-technician/test-details/<int:test_id>/', views.test_details, name='test_details'),
    path('lab-technician/update-results/<int:test_id>/', views.update_test_results, name='update_test_results'),
    path('lab-technician/patient-history/', views.lab_technician_patient_history, name='lab_technician_patient_history'),
    path('lab-technician/patient-history/<int:patient_id>/', views.lab_technician_patient_detail, name='lab_technician_patient_detail'),
    path('lab-technician/patient-pharmacy-queue/', views.patient_pharmacy_queue, name='patient_pharmacy_queue'),
    path('lab-technician/send-to-pharmacy/<int:patient_id>/', views.send_to_pharmacy, name='send_to_pharmacy'),
    
    # API URLs
    path('api/medication-schedules/', include('hospital.urls')),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)