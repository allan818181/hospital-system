from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'medication-schedules', views.MedicationScheduleViewSet, basename='medication-schedule')

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.staff_login, name='login'),
    
    # Dashboards
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Admin URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/staff/', views.staff_management, name='staff_management'),
    path('admin/staff/add/', views.add_staff, name='add_staff'),
    path('admin/staff/<int:user_id>/edit/', views.edit_staff, name='edit_staff'),
    path('admin/staff/<int:user_id>/delete/', views.delete_staff, name='delete_staff'),
    
    # Receptionist URLs
    path('receptionist/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('receptionist/patients/', views.patient_list, name='patient_list'),
    path('receptionist/patients/add/', views.add_patient, name='add_patient'),
    path('receptionist/patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('receptionist/patients/<int:pk>/edit/', views.edit_patient, name='edit_patient'),
    path('receptionist/appointments/', views.appointment_list, name='appointment_list'),
    path('receptionist/appointments/add/', views.add_appointment, name='add_appointment'),
    path('receptionist/patient-lab-queue/', views.patient_lab_queue, name='patient_lab_queue'),
    path('receptionist/send-to-lab/<int:patient_id>/', views.send_to_lab, name='send_to_lab'),
    
    # Doctor URLs
    path('doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/lab-test-results/', views.lab_test_results, name='lab_test_results'),
    path('doctor/consultation/<int:appointment_id>/', views.consultation, name='consultation'),
    path('doctor/request-lab-test/', views.request_lab_test, name='request_lab_test'),
    path('doctor/prescribe-after-lab/<int:test_id>/', views.prescribe_after_lab, name='prescribe_after_lab'),
    
    # Lab Technician URLs
    path('lab-technician/', views.lab_technician_dashboard, name='lab_technician_dashboard'),
    path('lab-technician/test-queue/', views.lab_test_queue, name='lab_test_queue'),
    path('lab-technician/test/<int:test_id>/', views.test_details, name='test_details'),
    path('lab-technician/test/<int:test_id>/update/', views.update_lab_test, name='update_lab_test'),
    path('lab-technician/pharmacy-queue/', views.patient_pharmacy_queue, name='patient_pharmacy_queue'),
    path('lab-technician/send-to-pharmacy/<int:patient_id>/', views.send_to_pharmacy, name='send_to_pharmacy'),
    path('lab-technician/patient-history/', views.lab_technician_patient_history, name='lab_technician_patient_history'),
    path('lab-technician/patient-history/<int:patient_id>/', views.lab_technician_patient_detail, name='lab_technician_patient_detail'),
    
    # Pharmacist URLs
    path('pharmacist/', views.pharmacist_dashboard, name='pharmacist_dashboard'),
    path('pharmacist/prescribe/<int:prescription_id>/', views.prescribe_medicine, name='prescribe_medicine'),
    path('pharmacist/schedule/<int:prescription_id>/', views.schedule_prescription, name='schedule_prescription'),
    path('pharmacist/prescriptions/', views.prescription_list, name='prescription_list'),
    path('pharmacist/prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('pharmacist/patient-history/', views.pharmacist_patient_history, name='pharmacist_patient_history'),
    path('pharmacist/patient-history/<int:patient_id>/', views.pharmacist_patient_detail, name='pharmacist_patient_detail'),
    
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # API Endpoints
    path('api/patient-medications/', views.patient_medications_api, name='patient_medications_api'),

    path('staff/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('staff/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('staff/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('staff/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('patient/medication-schedule/', views.patient_medication_schedule, name='patient_medication_schedule'),
    path('api/', include(router.urls)),
]
