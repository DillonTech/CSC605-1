from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from .forms import SignUpForm, UserProfileForm, StatementUploadForm
from .models import UserProfile
from .pdf_processor import StatementProcessor
from django.http import JsonResponse

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                UserProfile.objects.create(user=user)
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('home')
        except ValidationError as e:
            messages.error(request, str(e))
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def home_view(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    profile_form = UserProfileForm(instance=profile)
    statement_form = StatementUploadForm()

    if request.method == 'POST':
        if 'profile_update' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=profile)
            try:
                if profile_form.is_valid():
                    profile_form.save()
                    messages.success(request, 'Profile updated successfully!')
                else:
                    messages.error(request, 'Please correct the errors below.')
            except Exception as e:
                messages.error(request, f'Error updating profile: {str(e)}')
        
        elif 'statement_upload' in request.POST:
            statement_form = StatementUploadForm(request.POST, request.FILES)
            try:
                if statement_form.is_valid():
                    processor = StatementProcessor(profile)
                    processor.process_statement_async(request.FILES['statement_file'])
                    messages.success(request, 'Statement upload started! Processing...')
                else:
                    messages.error(request, 'Invalid file. Please upload a valid PDF.')
            except Exception as e:
                messages.error(request, f'Error processing statement: {str(e)}')

    context = {
        'profile_form': profile_form,
        'statement_form': statement_form,
        'profile': profile,
    }
    return render(request, 'home.html', context)

@login_required
def statement_status(request):
    """AJAX endpoint to check statement processing status"""
    profile = request.user.userprofile
    return JsonResponse({
        'status': profile.statement_processing_status,
        'error': profile.error_message if profile.statement_processing_status == 'error' else None
    })
