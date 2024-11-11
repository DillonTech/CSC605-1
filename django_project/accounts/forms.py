from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError
import magic  # for file type validation

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['monthly_income', 'currency', 'budget_style', 
                 'savings_goal_percentage', 'notification_email']
        widgets = {
            'monthly_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your monthly income'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'budget_style': forms.Select(attrs={'class': 'form-control'}),
            'savings_goal_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter savings goal percentage'
            }),
            'notification_email': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_savings_goal_percentage(self):
        percentage = self.cleaned_data.get('savings_goal_percentage')
        if percentage < 0 or percentage > 100:
            raise ValidationError("Savings goal must be between 0 and 100 percent.")
        return percentage

class StatementUploadForm(forms.Form):
    statement_file = forms.FileField(
        label='Upload Bank Statement (PDF)',
        help_text='Upload your bank statement in PDF format (max 10MB).',
        widget=forms.FileInput(attrs={
            'accept': 'application/pdf',
            'class': 'form-control'
        })
    )

    def clean_statement_file(self):
        file = self.cleaned_data.get('statement_file')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError("File size must be under 10MB.")
            
            # Check file type using python-magic
            file_type = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)  # Reset file pointer
            
            if file_type != 'application/pdf':
                raise ValidationError("Only PDF files are allowed.")
            
        return file
