from django import forms

from .models import Contact, Tag

class ContactForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['family_members'].queryset = Contact.objects.filter(user=user)
        self.fields['tags'].queryset = Tag.objects.filter(user=user)
        self.instance.user_id = user.id

    class Meta:
        model = Contact
        exclude = ['addresses', 'user']