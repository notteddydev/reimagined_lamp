from datetime import datetime

from django import forms
from django.conf import settings
from django.utils import translation

from phonenumber_field.formfields import localized_choices, PrefixChoiceField, SplitPhoneNumberField

from .constants import ADDRESS_TYPE__NAME_PREF, EMAIL_TYPE__NAME_PREF, PHONENUMBER_TYPE__NAME_PREF
from .models import Address, AddressType, Contact, Email, EmailType, PhoneNumber, PhoneNumberType, Tag, Tenancy, WalletAddress


class AddressForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["country"].empty_label = "-- Select Country --"
        self.fields["contacts"] = forms.ModelMultipleChoiceField(Contact.objects.filter(user=user))

        if self.instance.pk:
            self.fields["contacts"].initial = self.instance.contact_set.all()

    def save(self, commit=True):
        address = super().save(commit=commit)

        # Check for PK makes sure this only happens once address has been saved.
        if commit and address.pk:
            for tenancy in address.tenancy_set.all():
                if tenancy.contact_id not in self.cleaned_data["contacts"].values_list("id", flat=True):
                    tenancy.delete()

            for contact in self.cleaned_data["contacts"]:
                if contact.id not in address.tenancy_set.values_list("contact_id", flat=True):
                    Tenancy.objects.create(address=address, contact=contact)

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
        ("profession__name", "Profession"),
        ("addresses__state", "State"),
        ("tags__name", "Tag"),
        ("walletaddress__address", "Wallet Address"),
        ("year_met", "Year Met"),
    ]    
    filter_field = forms.ChoiceField(choices=FILTER_FIELD_CHOICES, required=False)
    filter_value = forms.CharField(required=False)

    def apply_filter(self, queryset):
        filter_field = self.cleaned_data.get("filter_field")
        filter_value = self.cleaned_data.get("filter_value")
            
        if filter_field and filter_value:
            queryset = queryset.filter(**{f"{filter_field}__icontains": filter_value})

        return queryset


class BaseContactFilterFormSet(forms.BaseFormSet):
    def apply_filters(self, queryset):
        for form in self:
            queryset = form.apply_filter(queryset)

        return queryset

ContactFilterFormSet = forms.formset_factory(ContactFilterForm, BaseContactFilterFormSet, extra=2)


class ContactForm(forms.ModelForm):
    def get_years_from_1920():
        return [year for year in range(1920, datetime.now().year + 1)][::-1]

    def __init__(self, user, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["profession"].empty_label = "-- Select Profession --"
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
    def clean(self):
        super().clean()
        pref_type = EmailType.objects.filter(name=EMAIL_TYPE__NAME_PREF).first()
        if pref_type:
            email_types = self.cleaned_data.get("email_types", [])
            if pref_type in email_types:
                if self.cleaned_data.get("archived", False):
                    self.add_error("email_types", "An email may not be 'preferred', and archived.")
                if len(email_types) == 1:
                    self.add_error("email_types", "'Preferred' is not allowed as the only type.")

    class Meta:
        model = Email
        exclude = ['contact']


class BaseEmailInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        pref_type = EmailType.objects.filter(name=EMAIL_TYPE__NAME_PREF).first()
        if pref_type:
            pref_count = 0
            unarchived_count = 0

            for form in self.forms:
                if not form.cleaned_data or form.cleaned_data.get("DELETE", False):
                    continue

                if pref_type in form.cleaned_data.get("email_types", []):
                    pref_count += 1

                if not form.cleaned_data.get("archived", False):
                    unarchived_count += 1

            if pref_count > 1:
                raise forms.ValidationError(f"Only one email may be designated as 'preferred'.")
            
            if pref_count < 1 <= unarchived_count:
                raise forms.ValidationError(f"One email must be designated as 'preferred'.")

EmailCreateFormSet = forms.inlineformset_factory(
    Contact,
    Email,
    form=EmailForm,
    formset=BaseEmailInlineFormSet,
    extra=3,
    can_delete=False
)
EmailUpdateFormSet = forms.inlineformset_factory(
    Contact,
    Email,
    form=EmailForm,
    formset=BaseEmailInlineFormSet,
    extra=3,
    can_delete=True
)


class CustomSplitPhoneNumberField(SplitPhoneNumberField):
    def prefix_field(self):
        language = translation.get_language() or settings.LANGUAGE_CODE
        choices = localized_choices(language)
        choices[0] = ("", "-- Select Country Prefix --")
        choices.sort(key=lambda item: item[1])

        return PrefixChoiceField(choices=choices)


class PhoneNumberForm(forms.ModelForm):
    number = CustomSplitPhoneNumberField()

    def clean(self):
        super().clean()
        pref_type = PhoneNumberType.objects.filter(name=PHONENUMBER_TYPE__NAME_PREF).first()
        if pref_type:
            phonenumber_types = self.cleaned_data.get("phonenumber_types", [])
            if pref_type in phonenumber_types:
                if self.cleaned_data.get("archived", False):
                    self.add_error("phonenumber_types", "A phone number may not be 'preferred', and archived.")
                if len(phonenumber_types) == 1:
                    self.add_error("phonenumber_types", "'Preferred' is not allowed as the only type.")

    class Meta:
        model = PhoneNumber
        exclude = ['address', 'contact']


class BasePhoneNumberInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        pref_type = PhoneNumberType.objects.filter(name=PHONENUMBER_TYPE__NAME_PREF).first()
        if pref_type:
            pref_count = 0
            unarchived_count = 0

            for form in self.forms:
                if not form.cleaned_data or form.cleaned_data.get("DELETE", False):
                    continue

                if pref_type in form.cleaned_data.get("phonenumber_types", []):
                    pref_count += 1

                if not form.cleaned_data.get("archived", False):
                    unarchived_count += 1

            if pref_count > 1:
                raise forms.ValidationError(f"Only one phone number may be designated as 'preferred'.")
            
            if pref_count < 1 <= unarchived_count:
                raise forms.ValidationError(f"One phone number must be designated as 'preferred'.")


ContactPhoneNumberCreateFormSet = forms.inlineformset_factory(
    Contact,
    PhoneNumber,
    form=PhoneNumberForm,
    formset=BasePhoneNumberInlineFormSet,
    extra=3,
    can_delete=False
)
ContactPhoneNumberUpdateFormSet = forms.inlineformset_factory(
    Contact,
    PhoneNumber,
    form=PhoneNumberForm,
    formset=BasePhoneNumberInlineFormSet,
    extra=3,
    can_delete=True
)
AddressPhoneNumberCreateFormSet = forms.inlineformset_factory(
    Address,
    PhoneNumber,
    form=PhoneNumberForm,
    formset=BasePhoneNumberInlineFormSet,
    extra=2,
    can_delete=False
)
AddressPhoneNumberUpdateFormSet = forms.inlineformset_factory(
    Address,
    PhoneNumber,
    form=PhoneNumberForm,
    formset=BasePhoneNumberInlineFormSet,
    extra=2,
    can_delete=True
)

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
    def __init__(self, *args, **kwargs):
        super(WalletAddressForm, self).__init__(*args, **kwargs)
        self.fields["network"].empty_label = "-- Select Network --"

    class Meta:
        model = WalletAddress
        exclude = ['contact']

WalletAddressCreateFormSet = forms.inlineformset_factory(Contact, WalletAddress, WalletAddressForm, extra=1, can_delete=False)
WalletAddressUpdateFormSet = forms.inlineformset_factory(Contact, WalletAddress, WalletAddressForm, extra=1, can_delete=True)