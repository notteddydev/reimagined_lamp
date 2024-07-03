from datetime import datetime

from django import forms

from phonenumber_field.formfields import SplitPhoneNumberField

from .models import Address, Contact, Email, PhoneNumber, Tag, WalletAddress


class AddressForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["contacts"] = forms.ModelMultipleChoiceField(Contact.objects.filter(user=user))

        if self.instance.pk:
            self.fields["contacts"].initial = self.instance.contact_set.all()

        if self.instance and self.instance.landline:
            self.fields["landline_number"].initial = self.instance.landline.number

    landline_number = SplitPhoneNumberField(**{"required": False})

    def save(self, commit=True):
        address = super().save(commit=False)
        old_landline = address.landline
        landline_number = self.cleaned_data["landline_number"]
        address.contact_set.set(self.cleaned_data["contacts"])

        if not len(landline_number):
            landline = None
        elif address.landline:
            landline = address.landline
            landline.number = landline_number
        else:
            landline = PhoneNumber(number=landline_number)
        
        address.landline = landline

        if commit:
            if old_landline and not landline:
                old_landline.delete()
            if landline:
                landline.save()
            address.save()
            
            # Check for PK makes sure this only happens once address has been saved.
            if address.pk:
                self.save_m2m()

        return address

    class Meta:
        model = Address
        exclude = ['landline', 'user']


class ContactFilterForm(forms.Form):
    FILTER_FIELD_CHOICES = [
        ("", "-- Select Field --"),
        ("email__email", "Email"),
        ("first_name", "First Name"),
        ("addresses__landline__number", "Landline"),
        ("last_name", "Last Name"),
        ("nationality__verbose", "Nationality"),
        ("nickname", "Nickname"),
        ("phonenumber__number", "Phone Number"),
        ("profession", "Profession"),
        ("tags__name", "Tag"),
        ("walletaddress__address", "Wallet Address"),
        ("year_met", "Year Met"),
    ]    
    filter_field = forms.ChoiceField(choices=FILTER_FIELD_CHOICES, required=False)
    filter_value = forms.CharField(required=False)


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
        exclude = ['user']

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


class WalletAddressForm(forms.ModelForm):
    class Meta:
        model = WalletAddress
        exclude = ['contact']

WalletAddressCreateFormSet = forms.inlineformset_factory(Contact, WalletAddress, WalletAddressForm, extra=1, can_delete=False)
WalletAddressUpdateFormSet = forms.inlineformset_factory(Contact, WalletAddress, WalletAddressForm, extra=1, can_delete=True)