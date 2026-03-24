from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Doctor, Pharmacist, Receptionist

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )

admin.site.register(User, CustomUserAdmin)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number')
    raw_id_fields = ('user',)

@admin.register(Pharmacist)
class PharmacistAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number')
    raw_id_fields = ('user',)

@admin.register(Receptionist)
class ReceptionistAdmin(admin.ModelAdmin):
    list_display = ('user',)
    raw_id_fields = ('user',)