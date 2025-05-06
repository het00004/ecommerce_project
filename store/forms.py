from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import DeliveryInfo

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class LoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
class DeliveryInfoForm(forms.ModelForm):
    class Meta:
        model = DeliveryInfo
        fields = ['state', 'city', 'address', 'pin_code', 'phone_number']
class CouponApplyForm(forms.Form):
    code = forms.CharField()