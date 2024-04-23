# forms.py
from django import forms
from accounts.models import Account

class EditUserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [ 'email', 'first_name', 'last_name']  
    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field_name.replace('_', ' ').title()