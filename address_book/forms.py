from django import forms

from phonenumber_field.formfields import SplitPhoneNumberField

from .models import Contact, PhoneNumber, Tag

class PhoneNumberForm(forms.ModelForm):
    number = SplitPhoneNumberField()

    class Meta:
        model = PhoneNumber
        exclude = ['contact']

class ContactForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields['tags'].queryset = Tag.objects.filter(user=user.id)
        self.fields['family_members'].queryset = Contact.objects.filter(user=user.id)

    class Meta:
        model = Contact
        exclude = ['addresses', 'user']

PhoneNumberCreateFormSet = forms.inlineformset_factory(Contact, PhoneNumber, PhoneNumberForm, extra=3, can_delete=False)
PhoneNumberUpdateFormSet = forms.inlineformset_factory(Contact, PhoneNumber, PhoneNumberForm, extra=3, can_delete=True)