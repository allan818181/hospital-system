from django import forms
from .models import LabTest, StaffProfile

class LabTestResultForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ['results']
        widgets = {
            'results': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter test results and measurements...'})
        }

class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = ['profile_picture', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        } 