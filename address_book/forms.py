from django import forms

from .models import Contact, Tag

class ContactForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['family_members'].queryset = Contact.objects.filter(user=self.initial['user'])
        self.fields['tags'].queryset = Tag.objects.filter(user=self.initial['user'])

    class Meta:
        model = Contact
        exclude = ['addresses', 'user']