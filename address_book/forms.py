from datetime import datetime

from django import forms

from phonenumber_field.formfields import SplitPhoneNumberField

from .models import Address, Contact, ContactAddress, Email, PhoneNumber, Tag, WalletAddress


class AddressForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["contacts"] = forms.ModelMultipleChoiceField(Contact.objects.filter(user=user))

        if self.instance.pk:
            self.fields["contacts"].initial = self.instance.contact_set.all()

    def save(self, commit=True):
        address = super().save(commit=commit)

        # Check for PK makes sure this only happens once address has been saved.
        if commit and address.pk:
            for contactaddress in address.contactaddress_set.all():
                if contactaddress.contact_id not in self.cleaned_data["contacts"].values_list("id", flat=True):
                    contactaddress.delete()

            for contact in self.cleaned_data["contacts"]:
                if contact.id not in address.contactaddress_set.values_list("contact_id", flat=True):
                    ContactAddress.objects.create(address=address, contact=contact)

        return address

    class Meta:
        model = Address
        exclude = ['user']


class ContactFilterForm(forms.Form):
    FILTER_FIELD_CHOICES = [
        ("", "-- Select Field --"),
        ("addresses__city", "City"),
        ("addresses__country__verbose", "Country"),
        ("email__email", "Email"),
        ("first_name", "First Name"),
        ("addresses__landline__number", "Landline"),
        ("last_name", "Last Name"),
        ("nationality__verbose", "Nationality"),
        ("addresses__neighbourhood", "Neighbourhood"),
        ("nickname", "Nickname"),
        ("phonenumber__number", "Phone Number"),
        ("profession", "Profession"),
        ("addresses__state", "State"),
        ("tags__name", "Tag"),
        ("walletaddress__address", "Wallet Address"),
        ("year_met", "Year Met"),
    ]    
    filter_field = forms.ChoiceField(choices=FILTER_FIELD_CHOICES, required=False)
    filter_value = forms.CharField(required=False)


class ContactForm(forms.ModelForm):
    def get_years_from_1920():
        return [year for year in range(1920, datetime.now().year + 1)][::-1]

    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields['tags'].queryset = Tag.objects.filter(user=user.id)
        self.fields['family_members'].queryset = Contact.objects.filter(user=user.id)

    anniversary = forms.DateField(
        required=False,
        widget=forms.widgets.SelectDateWidget(
            empty_label=("-- Select Year --", "-- Select Month --", "-- Select Day --"),
            years=get_years_from_1920(),
        )
    )
    dob = forms.DateField(
        required=False,
        widget=forms.widgets.SelectDateWidget(
            empty_label=("-- Select Year --", "-- Select Month --", "-- Select Day --"),
            years=get_years_from_1920(),
        )
    )
    dod = forms.DateField(
        required=False,
        widget=forms.widgets.SelectDateWidget(
            empty_label=("-- Select Year --", "-- Select Month --", "-- Select Day --"),
            years=get_years_from_1920(),
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
        exclude = ['address', 'contact']

ContactPhoneNumberCreateFormSet = forms.inlineformset_factory(Contact, PhoneNumber, PhoneNumberForm, extra=3, can_delete=False)
ContactPhoneNumberUpdateFormSet = forms.inlineformset_factory(Contact, PhoneNumber, PhoneNumberForm, extra=3, can_delete=True)
AddressPhoneNumberCreateFormSet = forms.inlineformset_factory(Address, PhoneNumber, PhoneNumberForm, extra=2, can_delete=False)
AddressPhoneNumberUpdateFormSet = forms.inlineformset_factory(Address, PhoneNumber, PhoneNumberForm, extra=2, can_delete=True)

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