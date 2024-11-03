from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

class CustomAuthenticationForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError(_('Invalid email or password'))
            elif not self.user.is_active:
                raise forms.ValidationError(_('This account is inactive.'))
            elif self.user.status == 'Blocked':
                raise forms.ValidationError(_('This account is blocked. Please contact support.'))

        return cleaned_data

    def get_user(self):
        return self.user if hasattr(self, 'user') else None