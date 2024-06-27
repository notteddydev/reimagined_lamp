from datetime import datetime

from django import forms

from phonenumber_field.formfields import SplitPhoneNumberField

from .models import Contact, Email, PhoneNumber, Tag

class ContactForm(forms.ModelForm):
    def get_years_for_dob_and_dod():
        return [year for year in range(1920, datetime.now().year + 1)][::-1]

    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields['tags'].queryset = Tag.objects.filter(user=user.id)
        self.fields['family_members'].queryset = Contact.objects.filter(user=user.id)

    dob = forms.DateField(
        required=False,
        widget=forms.widgets.SelectDateWidget(
            empty_label=("-- Select Year --", "-- Select Month --", "-- Select Day --"),
            years=get_years_for_dob_and_dod(),
        )
    )
    dod = forms.DateField(
        required=False,
        widget=forms.widgets.SelectDateWidget(
            empty_label=("-- Select Year --", "-- Select Month --", "-- Select Day --"),
            years=get_years_for_dob_and_dod(),
        )
    )

    class Meta:
        model = Contact
        exclude = ['addresses', 'user']

class EmailForm(forms.ModelForm):
    class Meta:
        model = Email
        exclude = ['contact']

EmailCreateFormSet = forms.inlineformset_factory(Contact, Email, EmailForm, extra=3, can_delete=False)
EmailUpdateFormSet = forms.inlineformset_factory(Contact, Email, EmailForm, extra=3, can_delete=True)

class PhoneNumberForm(forms.ModelForm):
    number = SplitPhoneNumberField()

    class Meta:
        model = PhoneNumber
        exclude = ['contact']

PhoneNumberCreateFormSet = forms.inlineformset_factory(Contact, PhoneNumber, PhoneNumberForm, extra=3, can_delete=False)
PhoneNumberUpdateFormSet = forms.inlineformset_factory(Contact, PhoneNumber, PhoneNumberForm, extra=3, can_delete=True)

class TagForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields['contacts'] = forms.ModelMultipleChoiceField(
            queryset=Contact.objects.filter(user=user),
            widget=forms.CheckboxSelectMultiple
        )

    class Meta:
        model = Tag
        exclude = ['user']