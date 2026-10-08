from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import User, Patient, Doctor, Pharmacist, Appointment, Prescription, MedicationSchedule, LabTest, Receptionist, StaffProfile, LabTechnician
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from .forms import LabTestResultForm, StaffProfileForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
import json
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import MedicationScheduleSerializer

def home(request):
    # Always show home page first, regardless of authentication status
    return render(request, 'home.html')


def staff_login(request):
    if request.user.is_authenticated:
        if request.user.role == 'RECEPTIONIST':
            return redirect('receptionist_dashboard')
        elif request.user.role == 'DOCTOR':
            return redirect('doctor_dashboard')
        elif request.user.role == 'PHARMACIST':
            return redirect('pharmacist_dashboard')
        elif request.user.is_superuser:
            return redirect('admin_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('admin_dashboard')
            elif user.role in ['DOCTOR', 'RECEPTIONIST', 'PHARMACIST', 'LAB_TECHNICIAN']:
                login(request, user)
                if user.role == 'DOCTOR':
                    return redirect('doctor_dashboard')
                elif user.role == 'RECEPTIONIST':
                    return redirect('receptionist_dashboard')
                elif user.role == 'PHARMACIST':
                    return redirect('pharmacist_dashboard')
                elif user.role == 'LAB_TECHNICIAN':
                    return redirect('lab_technician_dashboard')
            else:
                messages.error(request, 'Invalid role for staff login.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

@login_required
def patient_medication_schedule(request):
    return render(request, )


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard_redirect(request):
    if request.user.role == 'RECEPTIONIST':
        return redirect('receptionist_dashboard')
    elif request.user.role == 'DOCTOR':
        return redirect('doctor_dashboard')
    elif request.user.role == 'PHARMACIST':
        return redirect('pharmacist_dashboard')
    elif request.user.is_superuser:
        return redirect('admin:index')
    else:
        messages.error(request, 'Invalid role.')
        return redirect('home')

@login_required
def receptionist_dashboard(request):
    if request.user.role != 'RECEPTIONIST':
        return redirect('home')
    
    # Get all appointments
    appointments = Appointment.objects.all().order_by('-date_time')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query)
        )
    
    context = {
        'appointments': appointments,
        'search_query': search_query
    }
    return render(request, 'receptionist/dashboard.html', context)

@login_required
def doctor_dashboard(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    
    doctor = Doctor.objects.get(user=request.user)
    appointments = Appointment.objects.filter(doctor=doctor).order_by('-date_time')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        appointments = appointments.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query)
        )
    
    context = {
        'appointments': appointments,
        'search_query': search_query
    }
    return render(request, 'doctor/dashboard.html', context)

@login_required
def pharmacist_dashboard(request):
    if request.user.role != 'PHARMACIST':
        return redirect('home')
    
    # Get all suggested medicines that need to be prescribed
    suggested_medicines = Prescription.objects.filter(
        status='SUGGESTED'
    ).select_related(
        'appointment__patient__user',
        'prescribed_by__user'
    ).order_by('-created_at')
    
    # Get all prescriptions that need scheduling
    prescriptions_to_schedule = Prescription.objects.filter(
        status='PRESCRIBED',
        schedules__isnull=True
    ).select_related(
        'appointment__patient__user',
        'prescribed_by__user'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        suggested_medicines = suggested_medicines.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query) |
            Q(medication_name__icontains=search_query)
        )
        prescriptions_to_schedule = prescriptions_to_schedule.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query) |
            Q(medication_name__icontains=search_query)
        )
    
    return render(request, 'pharmacist/dashboard.html', {
        'suggested_medicines': suggested_medicines,
        'prescriptions_to_schedule': prescriptions_to_schedule,
        'search_query': search_query
    })

@login_required
def add_patient(request):
    if request.user.role != 'RECEPTIONIST':
        raise PermissionDenied("You don't have permission to access this page.")
        
    if request.method == 'POST':
        try:
            # Generate username from first name and last name
            first_name = request.POST.get('first_name').lower()
            last_name = request.POST.get('last_name').lower()
            base_username = f"{first_name}.{last_name}"
            username = base_username
            counter = 1
            
            # Keep trying until we find a unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Generate email from username
            email = f"{username}@meditrack.com"
            
            # Generate a random password
            random_password = get_random_string(12)  # 12 characters long
            
            # Create the User first
            user = User.objects.create_user(
                username=username,
                email=email,
                password=random_password,
                first_name=first_name,
                last_name=last_name,
                phone=request.POST.get('phone'),
                role='PATIENT'
            )
            
            # Then create the Patient
            patient = Patient.objects.create(
                user=user,
                address=request.POST.get('address'),
                date_of_birth=request.POST.get('date_of_birth'),
                gender=request.POST.get('gender'),
                emergency_contact=request.POST.get('emergency_contact')
            )
            
            messages.success(request, f'Patient registered successfully! Username: {username}, Password: {random_password}')
            return redirect('patient_list')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'receptionist/add_patient.html', {
                'form_data': request.POST
            })
    
    return render(request, 'receptionist/add_patient.html')

@login_required
def create_appointment(request):
    if request.user.role != 'RECEPTIONIST':
        raise PermissionDenied("You don't have permission to access this page.")
        
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        doctor_id = request.POST.get('doctor')
        date_time = request.POST.get('appointment_time')
        
        # Check if doctor is available
        conflicting_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            date_time=date_time
        ).exists()
        
        if not conflicting_appointments:
            Appointment.objects.create(
                patient_id=patient_id,
                doctor_id=doctor_id,
                date_time=date_time,
                status='SCHEDULED'
            )
            messages.success(request, 'Appointment booked!')
        else:
            messages.error(request, 'Doctor unavailable at this time')
    return redirect('appointment_list')


@login_required
def patient_list(request):
    if request.user.role != 'RECEPTIONIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    search_query = request.GET.get('search', '')
    if search_query:
        patients = Patient.objects.filter(
            user__first_name__icontains=search_query
        ) | Patient.objects.filter(
            user__last_name__icontains=search_query
        )
    else:
        patients = Patient.objects.all()
    
    return render(request, 'receptionist/patient_list.html', {
        'patients': patients,
        'search_query': search_query
    })

@login_required
def appointment_list(request):
    if request.user.role != 'RECEPTIONIST':
        raise PermissionDenied("You don't have permission to access this page.")
    appointments = Appointment.objects.all()
    return render(request, 'receptionist/appointment_list.html', {
        'appointments': appointments
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Patient, Appointment, Prescription

@login_required
def patient_detail(request, pk):
    if request.user.role not in ['RECEPTIONIST', 'DOCTOR', 'PHARMACIST', 'LAB_TECHNICIAN']:
        raise PermissionDenied("You don't have permission to access this page.")
    
    patient = get_object_or_404(Patient, pk=pk)
    appointments = Appointment.objects.filter(patient=patient).order_by('-date_time')
    prescriptions = Prescription.objects.filter(appointment__patient=patient)
    
    context = {
        'patient': patient,
        'appointments': appointments,
        'prescriptions': prescriptions,
    }
    return render(request, 'receptionist/patient_detail.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Patient, Doctor, Appointment

@login_required
def add_appointment(request):
    if request.user.role != 'RECEPTIONIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    patients = Patient.objects.all()
    doctors = Doctor.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            patient_id = request.POST.get('patient')
            doctor_id = request.POST.get('doctor')
            date_time = request.POST.get('date_time')
            reason = request.POST.get('reason')
            
            # Validate required fields
            if not all([patient_id, doctor_id, date_time, reason]):
                raise ValueError("All fields are required")
            
            # Create appointment
            Appointment.objects.create(
                patient_id=patient_id,
                doctor_id=doctor_id,
                date_time=date_time,
                reason=reason,
                status='SCHEDULED'
            )
            
            messages.success(request, 'Appointment created successfully!')
            return redirect('appointment_list')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'receptionist/add_appointment.html', {
        'patients': patients,
        'doctors': doctors
    })

@login_required
def prescription_list(request):
    if request.user.role not in ['DOCTOR', 'PHARMACIST']:
        return redirect('home')
    
    prescriptions = Prescription.objects.select_related(
        'appointment__patient__user',
        'appointment__doctor__user'
    ).order_by('-appointment__date_time')
    
    context = {
        'prescriptions': prescriptions,
        'user_role': request.user.role
    }
    return render(request, 'doctor/add_prescription.html', context)

@login_required
def prescription_detail(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    return render(request, 'hospital/prescription_detail.html', {
        'prescription': prescription
    })

@login_required
def schedule_medication(request, prescription_id):
    if request.user.role != 'PHARMACIST':
        return redirect('home')
    
@login_required
def add_schedule(request, prescription_id):
    if request.user.role != 'PHARMACIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    prescription = get_object_or_404(Prescription, pk=prescription_id)
    
    if request.method == 'POST':
        try:
            # Get time slots from the form (multiple inputs)
            time_slots = request.POST.getlist('time_slots')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            instructions = request.POST.get('instructions', '')
            
            if not all([time_slots, start_date, end_date]):
                raise ValueError("All required fields must be filled")
            
            # Create the schedule
            MedicationSchedule.objects.create(
                prescription=prescription,
                time_slots=time_slots,
                start_date=start_date,
                end_date=end_date,
                additional_instructions=instructions
            )
            
            messages.success(request, 'Medication schedule created successfully!')
            return redirect('pharmacist_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating schedule: {str(e)}')
    
    # Generate default times (8am, 2pm, 8pm)
    default_times = [
        (timezone.now() + timezone.timedelta(hours=8)).strftime('%H:%M'),
        (timezone.now() + timezone.timedelta(hours=14)).strftime('%H:%M'),
        (timezone.now() + timezone.timedelta(hours=20)).strftime('%H:%M')
    ]
    
    return render(request, 'pharmacist/add_schedule.html', {
        'prescription': prescription,
        'patient': prescription.appointment.patient,
        'default_times': default_times,
        'default_start': timezone.now().date(),
        'default_end': (timezone.now() + timezone.timedelta(days=7)).date()
    })

@login_required
def add_prescription(request, appointment_id):
    if request.user.role != 'PHARMACIST':
        return redirect('home')
    
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    
    if request.method == 'POST':
        try:
            medicine = request.POST.get('medicine')
            dosage = request.POST.get('dosage')
            frequency = request.POST.get('frequency')
            duration = request.POST.get('duration')
            notes = request.POST.get('notes', '')
            
            if not all([medicine, dosage, frequency, duration]):
                raise ValueError("All required fields must be filled")
            
            # Get the doctor who originally prescribed
            original_prescription = Prescription.objects.filter(appointment=appointment).first()
            if not original_prescription:
                raise ValueError("No original prescription found")
            
            Prescription.objects.create(
                appointment=appointment,
                medicine=medicine,
                dosage=dosage,
                frequency=frequency,
                duration=duration,
                notes=notes,
                prescribed_by=original_prescription.prescribed_by
            )
            
            messages.success(request, 'Additional prescription added successfully!')
            return redirect('pharmacist_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating prescription: {str(e)}')
    
    return render(request, 'pharmacist/add_prescription.html', {
        'appointment': appointment,
        'patient': appointment.patient
    })

@login_required
def patient_medications_api(request):
    """API endpoint for patient medications (mobile app)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if hasattr(request.user, 'patient'):
        prescriptions = Prescription.objects.filter(
            appointment__patient=request.user.patient
        ).values('medicine', 'dosage', 'frequency')
        return JsonResponse(list(prescriptions), safe=False)
    
    return JsonResponse({'error': 'Patient not found'}, status=404)

from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    if request.user.role == 'DOCTOR':
        return redirect('doctor_dashboard')
    elif request.user.role == 'PHARMACIST':
        return redirect('pharmacist_dashboard')
    elif request.user.role == 'RECEPTIONIST':
        return redirect('receptionist_dashboard')
    else:
        return redirect('admin:index')

@login_required
def consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if the user is a doctor and is assigned to this appointment
    if request.user.role != 'DOCTOR' or request.user.doctor != appointment.doctor:
        messages.error(request, "You don't have permission to access this consultation.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_lab_test':
            test_name = request.POST.get('test_name')
            instructions = request.POST.get('instructions')
            measurements = request.POST.get('measurements', '').strip()
            
            if test_name and instructions:
                # Create a new lab test with PENDING status
                measurements_list = [m.strip() for m in measurements.split(',') if m.strip()]
                lab_test = LabTest.objects.create(
                    appointment=appointment,
                    test_name=test_name,
                    instructions=instructions,
                    required_measurements=', '.join(measurements_list),
                    status='PENDING',
                    requested_by=request.user.doctor
                )
                messages.success(request, f"Test '{test_name}' added successfully.")
            else:
                messages.error(request, "Please fill in all required fields.")
                
        elif action == 'remove_test':
            test_id = request.POST.get('test_id')
            try:
                test = LabTest.objects.get(id=test_id, appointment=appointment, status='PENDING')
                test.delete()
                messages.success(request, "Test removed successfully.")
            except LabTest.DoesNotExist:
                messages.error(request, "Test not found.")
                
        elif action == 'submit_tests':
            # Submit all pending tests to the lab
            pending_tests = LabTest.objects.filter(
                appointment=appointment,
                status='PENDING'
            )
            if pending_tests.exists():
                pending_tests.update(status='IN_PROGRESS')
                messages.success(request, f"{pending_tests.count()} tests submitted to lab successfully.")
            else:
                messages.warning(request, "No pending tests to submit.")
                
        elif action == 'suggest_medicine':
            try:
                medication_name = request.POST.get('medication_name')
                dosage = request.POST.get('dosage')
                frequency = request.POST.get('frequency')
                duration = request.POST.get('duration')
                instructions = request.POST.get('instructions')
                
                prescription = Prescription.objects.create(
                    appointment=appointment,
                    medication_name=medication_name,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                    instructions=instructions,
                    prescribed_by=request.user.doctor,
                    status='SUGGESTED'
                )
                
                messages.success(request, 'Medicine suggested successfully!')
                return redirect('consultation', appointment_id=appointment_id)
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                
        elif action == 'add_notes':
            notes = request.POST.get('notes')
            if notes:
                appointment.notes = notes
                appointment.save()
                messages.success(request, "Notes saved successfully.")
            else:
                messages.error(request, "Please enter consultation notes.")
                
        elif action == 'complete':
            if not appointment.notes:
                messages.error(request, "Please add consultation notes before completing.")
            else:
                appointment.status = 'COMPLETED'
                appointment.save()
                messages.success(request, "Consultation completed successfully.")
                return redirect('doctor_dashboard')
    
    # Get all lab tests for this appointment
    lab_tests = LabTest.objects.filter(appointment=appointment).exclude(status='PENDING').order_by('-created_at')
    pending_tests = LabTest.objects.filter(appointment=appointment, status='PENDING').order_by('-created_at')
    
    # Get all suggested medicines for this appointment
    suggested_medicines = Prescription.objects.filter(
        appointment=appointment,
        status='SUGGESTED'
    ).order_by('-created_at')
    
    return render(request, 'doctor/consultation.html', {
        'appointment': appointment,
        'lab_tests': lab_tests,
        'pending_tests': pending_tests,
        'suggested_medicines': suggested_medicines
    })

@login_required
def prescribe_medicine(request, prescription_id):
    if request.user.role != 'PHARMACIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    prescription = get_object_or_404(Prescription, pk=prescription_id, status='SUGGESTED')

    pharmacist, created = Pharmacist.objects.get_or_create(
        user=request.user,
        defaults={
            'license_number': 'TEMP-' + str(request.user.id),
            'shift_schedule': 'Default'
        }
    )

    if request.method == 'POST':
        try:
            # Update prescription details
            prescription.dosage = request.POST.get('dosage')
            prescription.frequency = request.POST.get('frequency')
            prescription.duration = request.POST.get('duration')
            prescription.instructions = request.POST.get('instructions')
            prescription.status = 'PRESCRIBED'  # First set to PRESCRIBED
            prescription.save()

            # Get schedule details
            time_slots = request.POST.getlist('time_slots[]')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            if not all([time_slots, start_date, end_date]):
                raise ValueError("All schedule fields must be filled")

            # Create the medication schedule
            MedicationSchedule.objects.create(
                prescription=prescription,
                time_slots=time_slots,
                start_date=start_date,
                end_date=end_date,
                created_by=pharmacist
            )

            # Update prescription status to SCHEDULED after successful schedule creation
            prescription.status = 'SCHEDULED'
            prescription.save()

            messages.success(request, 'Medicine prescribed and scheduled successfully!')
            return redirect('pharmacist_dashboard')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            # Revert prescription status if there was an error
            prescription.status = 'SUGGESTED'
            prescription.save()

    return render(request, 'pharmacist/prescribe_medicine.html', {
        'prescription': prescription,
        'default_start': timezone.now().date(),
        'default_end': (timezone.now() + timezone.timedelta(days=7)).date()
    })

@login_required
def schedule_prescription(request, prescription_id):
    if request.user.role != 'PHARMACIST':
        return redirect('home')
    
    prescription = get_object_or_404(Prescription, pk=prescription_id, status='PRESCRIBED')
    
    if request.method == 'POST':
        try:
            # Get schedule details from form
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            reminder_times = request.POST.getlist('reminder_times')
            
            if not all([start_date, end_date, reminder_times]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('schedule_prescription', prescription_id=prescription_id)
            
            # Create schedule for the prescription
            schedule = MedicationSchedule.objects.create(
                prescription=prescription,
                time_slots=reminder_times,
                start_date=start_date,
                end_date=end_date
            )
            
            # Update prescription status
            prescription.status = 'SCHEDULED'
            prescription.save()
            
            messages.success(request, 'Prescription scheduled successfully!')
            return redirect('pharmacist_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error scheduling prescription: {str(e)}')
    
    return render(request, 'pharmacist/schedule_prescription.html', {
        'prescription': prescription
    })

@login_required
def edit_patient(request, pk):
    if request.user.role != 'RECEPTIONIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        try:
            # Update user information
            user = patient.user
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.phone = request.POST.get('phone')
            user.save()
            
            # Update patient information
            patient.address = request.POST.get('address')
            patient.date_of_birth = request.POST.get('date_of_birth')
            patient.gender = request.POST.get('gender')
            patient.emergency_contact = request.POST.get('emergency_contact')
            patient.save()
            
            messages.success(request, 'Patient information updated successfully!')
            return redirect('patient_detail', pk=patient.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating patient: {str(e)}')
    
    return render(request, 'receptionist/edit_patient.html', {
        'patient': patient
    })

@login_required
def lab_technician_dashboard(request):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset for lab tests
    lab_tests = LabTest.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS']
    ).select_related(
        'appointment__patient__user',
        'requested_by__user'
    )
    
    # Apply search filter if query exists
    if search_query:
        lab_tests = lab_tests.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query) |
            Q(test_name__icontains=search_query)
        )
    
    # Group tests by appointment
    tests_by_appointment = {}
    for test in lab_tests:
        appointment_id = test.appointment.id
        if appointment_id not in tests_by_appointment:
            tests_by_appointment[appointment_id] = {
                'patient': test.appointment.patient,
                'appointment': test.appointment,
                'tests': []
            }
        tests_by_appointment[appointment_id]['tests'].append(test)
    
    return render(request, 'lab_technician/dashboard.html', {
        'tests_by_appointment': tests_by_appointment,
        'search_query': search_query
    })

@login_required
@user_passes_test(lambda u: u.role == 'LAB_TECHNICIAN')
def update_lab_test(request, test_id):
    lab_test = get_object_or_404(LabTest, id=test_id)
    
    if request.method == 'POST':
        form = LabTestResultForm(request.POST, instance=lab_test)
        if form.is_valid():
            lab_test = form.save(commit=False)
            lab_test.status = 'COMPLETED'
            lab_test.save()
            messages.success(request, 'Lab test results updated successfully.')
            return redirect('lab_technician_dashboard')
    else:
        form = LabTestResultForm(instance=lab_test)
    
    return render(request, 'lab_technician/update_test.html', {
        'form': form,
        'lab_test': lab_test
    })

@login_required
def prescribe_after_lab(request, test_id):
    if request.user.role != 'DOCTOR':
        raise PermissionDenied("You don't have permission to access this page.")
    
    lab_test = get_object_or_404(LabTest, pk=test_id, requested_by__user=request.user)
    
    if request.method == 'POST':
        try:
            # Get list of medicine names
            medicines = request.POST.getlist('medicines[]')
            
            # Create prescriptions for each medicine
            prescriptions = []
            for medicine in medicines:
                prescription = Prescription.objects.create(
                    appointment=lab_test.appointment,
                    medication_name=medicine,
                    dosage='',  # Empty, to be filled by pharmacist
                    frequency='',  # Empty, to be filled by pharmacist
                    duration='',  # Empty, to be filled by pharmacist
                    instructions='',  # Empty, to be filled by pharmacist
                    prescribed_by=lab_test.requested_by,
                    status='SUGGESTED'  # Set initial status as SUGGESTED for pharmacist review
                )
                prescriptions.append(prescription)
            
            # Mark the appointment as completed
            lab_test.appointment.status = 'COMPLETED'
            lab_test.appointment.save()
            
            # Update patient status to send to pharmacy
            patient = lab_test.appointment.patient
            patient.status = 'IN_PHARMACY'
            patient.save()
            
            messages.success(request, f'Created {len(prescriptions)} prescriptions successfully! Patient has been sent to pharmacy.')
            return redirect('doctor_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error creating prescriptions: {str(e)}')
    
    return render(request, 'doctor/prescribe_after_lab.html', {
        'lab_test': lab_test,
        'patient': lab_test.appointment.patient
    })

@login_required
def patient_lab_queue(request):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    
    doctor = Doctor.objects.get(user=request.user)
    patients = Patient.objects.filter(
        appointments__doctor=doctor,
        status='WAITING'
    ).distinct()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        patients = patients.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    context = {
        'patients': patients,
        'search_query': search_query
    }
    return render(request, 'doctor/patient_lab_queue.html', context)

@login_required
def patient_pharmacy_queue(request):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset for patients
    patients = Patient.objects.filter(
        status__in=['IN_LAB', 'READY_FOR_PHARMACY']
    )
    
    # Apply search filter if query exists
    if search_query:
        patients = patients.filter(
            user__first_name__icontains=search_query
        ) | patients.filter(
            user__last_name__icontains=search_query
        )
    
    return render(request, 'lab_technician/patient_pharmacy_queue.html', {
        'patients': patients,
        'search_query': search_query
    })

@login_required
def send_to_lab(request, patient_id):
    if request.user.role != 'DOCTOR':
        return redirect('home')
    
    try:
        patient = Patient.objects.get(id=patient_id)
        patient.status = 'IN_LAB'
        patient.save()
        messages.success(request, f'{patient.user.get_full_name()} has been sent to the lab.')
    except Patient.DoesNotExist:
        messages.error(request, 'Patient not found.')
    
    return redirect('doctor_dashboard')

@login_required
def send_to_pharmacy(request, patient_id):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    patient = get_object_or_404(Patient, pk=patient_id)
    patient.status = 'IN_PHARMACY'
    patient.save()
    
    messages.success(request, f'Patient {patient.user.get_full_name()} sent to pharmacy.')
    return redirect('patient_pharmacy_queue')

@login_required
def request_lab_test(request):
    if request.user.role != 'DOCTOR':
        raise PermissionDenied("You don't have permission to access this page.")
    
    if request.method == 'POST':
        try:
            appointment_id = request.POST.get('appointment')
            test_name = request.POST.get('test_name')
            instructions = request.POST.get('instructions')
            
            if not all([appointment_id, test_name, instructions]):
                raise ValueError("All fields are required")
            
            appointment = get_object_or_404(Appointment, pk=appointment_id)
            
            # Create lab test request
            LabTest.objects.create(
                appointment=appointment,
                requested_by=request.user.doctor,
                test_name=test_name,
                instructions=instructions,
                status='PENDING'
            )
            
            messages.success(request, 'Lab test requested successfully!')
            return redirect('doctor_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    # Get all appointments for this doctor
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor,
        status='SCHEDULED'
    ).select_related(
        'patient__user'
    ).order_by('-date_time')
    
    return render(request, 'doctor/request_lab_test.html', {
        'appointments': appointments
    })

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Fix missing LabTechnician objects
    lab_tech_users = User.objects.filter(role='LAB_TECHNICIAN')
    for user in lab_tech_users:
        if not hasattr(user, 'labtechnician'):
            LabTechnician.objects.create(user=user)
    
    # Get counts for different staff types
    doctors_count = Doctor.objects.count()
    pharmacists_count = Pharmacist.objects.count()
    lab_technicians_count = LabTechnician.objects.count()
    receptionists_count = Receptionist.objects.count()
    
    # Debug: Check if there are users with LAB_TECHNICIAN role
    lab_tech_users_count = User.objects.filter(role='LAB_TECHNICIAN').count()
    
    # Get recent staff members from all roles
    recent_staff = []
    recent_staff.extend(Doctor.objects.all().order_by('-user__date_joined')[:5])
    recent_staff.extend(Pharmacist.objects.all().order_by('-user__date_joined')[:5])
    recent_staff.extend(LabTechnician.objects.all().order_by('-user__date_joined')[:5])
    recent_staff.extend(Receptionist.objects.all().order_by('-user__date_joined')[:5])
    
    # Sort by date joined and take the most recent 10
    recent_staff.sort(key=lambda x: x.user.date_joined, reverse=True)
    recent_staff = recent_staff[:10]
    
    context = {
        'doctors_count': doctors_count,
        'pharmacists_count': pharmacists_count,
        'lab_technicians_count': lab_technicians_count,
        'receptionists_count': receptionists_count,
        'recent_staff': recent_staff,
        'debug_lab_tech_users': lab_tech_users_count  # For debugging
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
def staff_management(request):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get all staff members
    staff_list = []
    staff_list.extend(Doctor.objects.all())
    staff_list.extend(Pharmacist.objects.all())
    staff_list.extend(LabTechnician.objects.all())
    staff_list.extend(Receptionist.objects.all())
    
    return render(request, 'admin/staff_management.html', {
        'staff_list': staff_list
    })

@login_required
def add_staff(request):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page.")
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            role = request.POST.get('role')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if not all([first_name, last_name, username, email, phone, role, password, confirm_password]):
                raise ValueError("All fields are required")
            
            if password != confirm_password:
                raise ValueError("Passwords do not match")
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                raise ValueError("Username already exists. Please choose a different username.")
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise ValueError("Email already exists. Please use a different email.")
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=role
            )
            
            # Create corresponding staff object based on role
            if role == 'DOCTOR':
                Doctor.objects.create(user=user)
            elif role == 'RECEPTIONIST':
                Receptionist.objects.create(user=user)
            elif role == 'LAB_TECHNICIAN':
                LabTechnician.objects.create(user=user)
            elif role == 'PHARMACIST':
                Pharmacist.objects.create(user=user)
            
            messages.success(request, f'Staff member {user.get_full_name()} added successfully!')
            return redirect('staff_management')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('staff_management')

@login_required
def edit_staff(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page.")
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            
            # Check if username already exists (excluding current user)
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                raise ValueError("Username already exists. Please choose a different username.")
            
            # Check if email already exists (excluding current user)
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                raise ValueError("Email already exists. Please use a different email.")
            
            # Update user information
            user.first_name = first_name
            user.last_name = last_name
            user.username = username
            user.email = email
            user.phone = phone
            
            # Update password if provided
            new_password = request.POST.get('new_password')
            if new_password:
                user.set_password(new_password)
            
            user.save()
            
            messages.success(request, f'Staff member {user.get_full_name()} updated successfully!')
            return redirect('staff_management')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'admin/edit_staff.html', {
        'staff_user': user
    })

@login_required
def delete_staff(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied("You don't have permission to access this page.")
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            user.delete()
            messages.success(request, f'Staff member deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('staff_management')

@login_required
def lab_test_queue(request):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset for lab tests
    lab_tests = LabTest.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS']
    ).select_related(
        'appointment__patient__user',
        'requested_by__user'
    )
    
    # Apply search filter if query exists
    if search_query:
        lab_tests = lab_tests.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query) |
            Q(test_name__icontains=search_query)
        )
    
    # Order tests by creation date
    lab_tests = lab_tests.order_by('-created_at')
    
    return render(request, 'lab_technician/lab_test_queue.html', {
        'lab_tests': lab_tests,
        'search_query': search_query
    })

@login_required
def test_details(request, test_id):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    lab_test = get_object_or_404(LabTest, pk=test_id)
    
    if request.method == 'POST':
        try:
            # Update test status and results
            lab_test.status = request.POST.get('status')
            lab_test.results = request.POST.get('results')
            lab_test.assigned_to = request.user.labtechnician
            lab_test.save()
            
            messages.success(request, 'Lab test updated successfully!')
            return redirect('lab_test_queue')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'lab_technician/test_details.html', {
        'lab_test': lab_test
    })

@login_required
def update_test_results(request, test_id):
    if request.user.role != 'LAB_TECHNICIAN':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
        
    lab_test = get_object_or_404(LabTest, id=test_id)
    
    if request.method == 'POST':
        try:
            # Update test results
            results = request.POST.get('results')
            if results:
                lab_test.results = results
                lab_test.status = 'COMPLETED'
                lab_test.save()
                messages.success(request, 'Test results updated successfully!')
                return redirect('lab_technician_dashboard')
            else:
                messages.error(request, 'Please enter test results.')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'lab_technician/update_test.html', {
        'lab_test': lab_test
    })

@login_required
def lab_test_results(request):
    if request.user.role != 'DOCTOR':
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get all lab tests for this doctor's patients
    lab_tests = LabTest.objects.filter(
        appointment__doctor=request.user.doctor
    ).select_related(
        'appointment__patient__user',
        'appointment'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        lab_tests = lab_tests.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query)
        )
    
    # Group tests by appointment
    tests_by_appointment = {}
    for test in lab_tests:
        appointment_id = test.appointment.id
        if appointment_id not in tests_by_appointment:
            tests_by_appointment[appointment_id] = {
                'patient': test.appointment.patient,
                'appointment': test.appointment,
                'tests': []
            }
        tests_by_appointment[appointment_id]['tests'].append(test)
    
    return render(request, 'doctor/lab_test_results.html', {
        'tests_by_appointment': tests_by_appointment,
        'search_query': search_query
    })

@login_required
def profile_view(request):
    try:
        profile = request.user.staff_profile
    except StaffProfile.DoesNotExist:
        profile = StaffProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = StaffProfileForm(instance=profile)
    
    return render(request, 'profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })

class MedicationScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PATIENT':
            # Patients can only see their own schedules
            return MedicationSchedule.objects.filter(
                prescription__appointment__patient__user=user
            ).order_by('-created_at')
        elif user.role == 'PHARMACIST':
            # Pharmacists can see all schedules they created
            return MedicationSchedule.objects.filter(
                created_by__user=user
            ).order_by('-created_at')
        elif user.role == 'DOCTOR':
            # Doctors can see schedules for prescriptions they suggested
            return MedicationSchedule.objects.filter(
                prescription__prescribed_by__user=user
            ).order_by('-created_at')
        return MedicationSchedule.objects.none()

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active medication schedules"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            start_date__lte=today,
            end_date__gte=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get all upcoming medication schedules"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            start_date__gt=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        """Get all past medication schedules"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            end_date__lt=today
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

@login_required
def lab_technician_patient_history(request):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all completed lab tests
    lab_tests = LabTest.objects.filter(
        status='COMPLETED'
    ).select_related(
        'appointment__patient__user',
        'requested_by__user'
    ).order_by('-created_at')
    
    # Apply search filter if query exists
    if search_query:
        lab_tests = lab_tests.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query) |
            Q(test_name__icontains=search_query)
        )
    
    # Group tests by patient
    tests_by_patient = {}
    for test in lab_tests:
        patient_id = test.appointment.patient.id
        if patient_id not in tests_by_patient:
            tests_by_patient[patient_id] = {
                'patient': test.appointment.patient,
                'tests': []
            }
        tests_by_patient[patient_id]['tests'].append(test)
    
    return render(request, 'lab_technician/patient_history.html', {
        'tests_by_patient': tests_by_patient,
        'search_query': search_query
    })

@login_required
def lab_technician_patient_detail(request, patient_id):
    if request.user.role != 'LAB_TECHNICIAN':
        raise PermissionDenied("You don't have permission to access this page.")
    
    patient = get_object_or_404(Patient, pk=patient_id)
    
    # Get all completed lab tests for this patient
    lab_tests = LabTest.objects.filter(
        appointment__patient=patient,
        status='COMPLETED'
    ).select_related(
        'appointment__doctor__user',
        'requested_by__user'
    ).order_by('-created_at')
    
    return render(request, 'lab_technician/patient_detail.html', {
        'patient': patient,
        'lab_tests': lab_tests
    })

@login_required
def pharmacist_patient_history(request):
    if request.user.role != 'PHARMACIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all scheduled prescriptions
    prescriptions = Prescription.objects.filter(
        status='SCHEDULED'
    ).select_related(
        'appointment__patient__user',
        'prescribed_by__user'
    ).order_by('-created_at')
    
    # Apply search filter if query exists
    if search_query:
        prescriptions = prescriptions.filter(
            Q(appointment__patient__user__first_name__icontains=search_query) |
            Q(appointment__patient__user__last_name__icontains=search_query) |
            Q(medication_name__icontains=search_query)
        )
    
    # Group prescriptions by patient
    prescriptions_by_patient = {}
    for prescription in prescriptions:
        patient_id = prescription.appointment.patient.id
        if patient_id not in prescriptions_by_patient:
            prescriptions_by_patient[patient_id] = {
                'patient': prescription.appointment.patient,
                'prescriptions': []
            }
        prescriptions_by_patient[patient_id]['prescriptions'].append(prescription)
    
    return render(request, 'pharmacist/patient_history.html', {
        'prescriptions_by_patient': prescriptions_by_patient,
        'search_query': search_query
    })

@login_required
def pharmacist_patient_detail(request, patient_id):
    if request.user.role != 'PHARMACIST':
        raise PermissionDenied("You don't have permission to access this page.")
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get all prescriptions and medication schedules for this patient
    prescriptions = Prescription.objects.filter(
        appointment__patient=patient
    ).select_related('prescribed_by__user', 'appointment__patient__user').order_by('-created_at')
    
    medication_schedules = MedicationSchedule.objects.filter(
        prescription__appointment__patient=patient
    ).select_related('created_by__user').order_by('-start_date')
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'medication_schedules': medication_schedules
    }
    return render(request, 'pharmacist/patient_detail.html', context)