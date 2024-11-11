from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
    ]

    BUDGET_STYLE_CHOICES = [
        ('50-30-20', '50/30/20 Rule'),
        ('70-20-10', '70/20/10 Rule'),
        ('ENVELOPE', 'Envelope Method'),
        ('CUSTOM', 'Custom Allocation'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_income = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    budget_style = models.CharField(
        max_length=20,
        choices=BUDGET_STYLE_CHOICES,
        default='50-30-20'
    )
    savings_goal_percentage = models.IntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    notification_email = models.BooleanField(default=True)
    last_statement_upload = models.DateTimeField(null=True, blank=True)
    statement_processing_status = models.CharField(
        max_length=20,
        default='none',
        choices=[
            ('none', 'No Statement'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('error', 'Error'),
        ]
    )
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
