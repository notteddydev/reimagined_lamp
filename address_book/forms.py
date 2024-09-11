from django import forms
from django.conf import settings
from django.db import models
from django.utils import translation

import datetime
from phonenumber_field.formfields import localized_choices, PrefixChoiceField, SplitPhoneNumberField

from typing import List, Optional

from .models import Address, AddressType, Contact, Email, EmailType, PhoneNumber, PhoneNumberType, Tag, Tenancy, User, WalletAddress
from .utils import get_years_from_year


def create_date_field(required: Optional[bool] = False, from_year: Optional[int] = 1920) -> forms.DateField:
    """
    Create a DateField for a form with consistent empty labels and a consistent list of years.
    """
    return forms.DateField(
        required=required,
        widget=forms.widgets.SelectDateWidget(
            empty_label=("-- Select Year --", "-- Select Month --", "-- Select Day --"),
            years=get_years_from_year(year=from_year),
        )
    )


class ContactableMixin:
    def clean(self) -> None:
        """
        Ensure that a Contactable, if associated with the 'preferred' ContactableType, is NOT archived,
        and is associated with at least one other ContactableType.
        """
        super().clean()
        if self.pref_contactable_type:
            contactable_types = self.cleaned_data.get(self.contactable_types_field_name, [])
            if self.pref_contactable_type in contactable_types:
                if self.cleaned_data.get("archived", False):
                    self.add_error(self.contactable_types_field_name, "Being 'preferred' and archived is not allowed.")
                if len(contactable_types) == 1:
                    self.add_error(self.contactable_types_field_name, "'Preferred' is not allowed as the only type.")


class ContactableFormSetMixin:
    def _get_contactable_type_errors(self) -> List[str]:
        """
        Ensure that in a ContactableFormSet, ONE UNARCHIVED Contactable is designated as 'preferred' -
        no less, and no more. If there are no unarchived Contactables, no errors are added here.
        The individual ContactableMixin takes care of ensuring that a Contactable is not 'preferred'
        and archived at the same time.

        Return an array of errors so that it can be concatenated with an array of any other errors which may
        exist in the FormSet.
        """
        errors = []

        if self.pref_contactable_type:
            pref_count = 0
            unarchived_count = 0

            for form in self.forms:
                if not form.cleaned_data or form.cleaned_data.get("DELETE", False):
                    continue

                if self.pref_contactable_type in form.cleaned_data.get(self.contactable_types_field_name, []):
                    pref_count += 1

                if not form.cleaned_data.get("archived", False):
                    unarchived_count += 1

            if pref_count > 1:
                errors.append(f"Only one may be designated as 'preferred'.")
            
            if pref_count < 1 <= unarchived_count:
                errors.append(f"One must be designated as 'preferred'.")

        return errors


class SaveFormSetIfNotEmptyMixin:
    def save_if_not_empty(self, instance: models.Model) -> List[models.Model]:
        """
        Ensures that a FormSet is not empty, before saving it.
        """
        has_valid_data = any(
            form.is_valid() and form.cleaned_data
            for form in self
        )

        if has_valid_data:
            self.instance = instance
            return self.save()
        
        return []


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ["user"]

    def __init__(self, user, *args, **kwargs):
        """
        Set the user_id on the instance using the user passed in, set the empty_label for the Country
        field.
        """
        super(AddressForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["country"].empty_label = "-- Select Country --"


class ContactFilterForm(forms.Form):
    FILTER_FIELD_CHOICES = [
        ("", "-- Select Field --"),
        ("addresses__city", "City"),
        ("addresses__country__verbose", "Country"),
        ("email__email", "Email"),
        ("first_name", "First Name"),
        ("addresses__landline__number", "Landline"),
        ("last_name", "Last Name"),
        ("nationalities__verbose", "Nationality"),
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

    def apply_filter(self, queryset: models.QuerySet[Contact]) -> models.QuerySet[Contact]:
        """
        Filter a Contact queryset based on the values passed into the Form.
        """
        filter_field = self.cleaned_data.get("filter_field")
        filter_value = self.cleaned_data.get("filter_value")
            
        if filter_field and filter_value:
            queryset = queryset.filter(**{f"{filter_field}__icontains": filter_value})

        return queryset


class BaseContactFilterFormSet(forms.BaseFormSet):
    def apply_filters(self, queryset: models.QuerySet[Contact]) -> models.QuerySet[Contact]:
        """
        Call the apply_filter method for each Form in the FormSet, filtering a Contact queryset
        based on the values passed into the FormSet.
        """
        for form in self:
            queryset = form.apply_filter(queryset)

        return queryset

ContactFilterFormSet = forms.formset_factory(ContactFilterForm, BaseContactFilterFormSet, extra=2)


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        exclude = ["addresses", "user"]

    anniversary = create_date_field()
    dob = create_date_field()
    dod = create_date_field()

    def __init__(self, user, *args, **kwargs):
        """
        Set the user_id for the instance using the User object passed in; filter Tags and FamilyMembers
        querysets to ensure that only Models owned by the passed in User are provided as options; set 
        the empty_label for 'Profession' field.
        """
        super(ContactForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["profession"].empty_label = "-- Select Profession --"
        self.fields["tags"].queryset = Tag.objects.filter(user=user.id)
        self.fields["family_members"].queryset = Contact.objects.filter(user=user.id)

    def clean(self) -> None:
        """
        Call the clean_dates method.
        """
        cleaned_data = super().clean()
        self.clean_dates(cleaned_data=cleaned_data)

    def clean_dates(self, cleaned_data: dict) -> None:
        """
        Clean the dates for the ContactForm, ensuring coherence of the 'year_met', 'dob', 'dod', and
        'anniversary' fields.
        """
        anniversary = cleaned_data.get("anniversary", None)
        dob = cleaned_data.get("dob", None)
        dod = cleaned_data.get("dod", None)
        year_met = cleaned_data.get("year_met", None)
            
        if dob:
            if anniversary and anniversary <= dob:
                self.add_error("anniversary", "Anniversary must be greater than the date of birth.")
            if dob > datetime.date.today():
                self.add_error("dob", "Date of birth may not be set to a future date.")
            if year_met and dob.year > year_met:
                self.add_error("year_met", "Year met may not be before the date of birth.")
        if dod:
            if anniversary and anniversary > dod:
                self.add_error("anniversary", "Anniversary must be sooner than the date of passing.")
            if dob and dob > dod:
                self.add_error("dob", "Date of birth may not be after date of passing.")
            if dod > datetime.date.today():
                self.add_error("dod", "Date of passing may not be set to a future date.")
            if year_met and dod.year < year_met:
                self.add_error("year_met", "Year met may not be after date of passing.")


class EmailForm(ContactableMixin, forms.ModelForm):
    class Meta:
        model = Email
        exclude = ["contact"]

    contactable_types_field_name = "email_types"
    pref_contactable_type = EmailType.objects.preferred().first()


class BaseEmailInlineFormSet(ContactableFormSetMixin, SaveFormSetIfNotEmptyMixin, forms.BaseInlineFormSet):
    contactable_types_field_name = "email_types"
    pref_contactable_type = EmailType.objects.preferred().first()

    def clean(self) -> None:
        """
        Call _get_contactable_type_errors method, and if it returns any errors, raise a validation error
        to display them.
        """
        super().clean()
        errors = self._get_contactable_type_errors()
        if errors:
            raise forms.ValidationError(errors)


EmailFormSet = forms.inlineformset_factory(
    Contact,
    Email,
    form=EmailForm,
    formset=BaseEmailInlineFormSet,
    extra=3
)


class CustomSplitPhoneNumberField(SplitPhoneNumberField):
    def prefix_field(self) -> PrefixChoiceField:
        """
        Set the empty_label (first, empty, choice) for the 'prefix_field', and sort the choices
        in alphabetical order as opposed to in order of the numeric code.
        """
        language = translation.get_language() or settings.LANGUAGE_CODE
        choices = localized_choices(language)
        choices[0] = ("", "-- Select Country Prefix --")
        choices.sort(key=lambda item: item[1])

        return PrefixChoiceField(choices=choices)


class PhoneNumberForm(ContactableMixin, forms.ModelForm):
    class Meta:
        model = PhoneNumber
        exclude = ["address", "contact"]

    contactable_types_field_name = "phonenumber_types"
    pref_contactable_type = PhoneNumberType.objects.preferred().first()

    number = CustomSplitPhoneNumberField()


class BasePhoneNumberInlineFormSet(ContactableFormSetMixin, SaveFormSetIfNotEmptyMixin, forms.BaseInlineFormSet):
    contactable_types_field_name = "phonenumber_types"
    pref_contactable_type = PhoneNumberType.objects.preferred().first()

    def clean(self) -> None:
        """
        Call _get_contactable_type_errors method, and if it returns any errors, raise a validation error
        to display them.
        """
        super().clean()
        errors = self._get_contactable_type_errors()
        if errors:
            raise forms.ValidationError(errors)


ContactPhoneNumberFormSet = forms.inlineformset_factory(
    Contact,
    PhoneNumber,
    form=PhoneNumberForm,
    formset=BasePhoneNumberInlineFormSet,
    extra=3
)
AddressPhoneNumberFormSet = forms.inlineformset_factory(
    Address,
    PhoneNumber,
    form=PhoneNumberForm,
    formset=BasePhoneNumberInlineFormSet,
    extra=2
)

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        exclude = ["user"]

    def __init__(self, user, *args, **kwargs):
        """
        Set the instance user_id using the User passed in; filter the Contacts queryset so that only
        Contacts owned by the logged in User are provided as choices; make sure that the initial value
        is set to the existing linked Contacts if there are any.
        """
        super(TagForm, self).__init__(*args, **kwargs)
        self.instance.user_id = user.id
        self.fields["contacts"] = forms.ModelMultipleChoiceField(
            initial=self.instance.contact_set.all() if self.instance.id else [],
            queryset=Contact.objects.filter(user=user),
            widget=forms.CheckboxSelectMultiple
        )

    def save(self, commit: bool = True) -> Tag:
        """
        Ensure that the Contact associations are updated upon save - both adding and removing Contact
        association where necessary.
        """
        tag = super().save(commit=commit)

        if commit:
            contacts_selected = self.cleaned_data["contacts"]
            for contact in self.instance.contact_set.all():
                if contact not in contacts_selected:
                    contact.tags.remove(tag)

            for contact in contacts_selected:
                contact.tags.add(tag)

        return tag


class TenancyForm(ContactableMixin, forms.ModelForm):
    class Meta:
        model = Tenancy
        exclude = ["contact"]

    contactable_types_field_name = "tenancy_types"
    pref_contactable_type = AddressType.objects.preferred().first()

    def __init__(self, *args, **kwargs):
        """
        Receive a User as an argument and use that to filter the queryset for the Address field to ensure
        that only Addresses owned by the logged in User are provided as choices.
        """
        user = kwargs.pop("user", None)
        if not user:
            raise TypeError("TenancyForm.__init__() missing 1 required keyword argument: 'user'")
        self.user = user
        super(TenancyForm, self).__init__(*args, **kwargs)

        self.fields["address"] = forms.ModelChoiceField(
            Address.objects.filter(user=self.user),
            empty_label="-- Select Address --"
        )


class BaseTenancyInlineFormSet(ContactableFormSetMixin, SaveFormSetIfNotEmptyMixin, forms.BaseInlineFormSet):
    contactable_types_field_name = "tenancy_types"
    pref_contactable_type = AddressType.objects.preferred().first()

    def __init__(self, *args, **kwargs):
        """
        Receive a User as an arg, necessary for passing into the individual forms to filter the Address
        querysets for the Address field.
        """
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i: int, **kwargs) -> TenancyForm:
        """
        Pass the User into each form instance to filter Address querysets.
        """
        kwargs["user"] = self.user
        return super()._construct_form(i, **kwargs)

    def clean(self) -> None:
        """
        Call _get_contactable_type_errors method, and if it returns any errors, concatenate them with any
        errors that may arise from an Address attempted to be linked to a Contact more than once, and raise
        a validation error displaying all errors, if there are any.
        """
        super().clean()
        errors = self._get_contactable_type_errors()

        addresses = []
        for form in self.forms:
            if form.cleaned_data and form.cleaned_data.get("address"):
                address = form.cleaned_data["address"]
                if address in addresses:
                    errors.append("An address may only be assigned to a contact once.")
                    break
                addresses.append(address)

        if errors:
            raise forms.ValidationError(errors)


TenancyFormSet = forms.inlineformset_factory(
    Contact,
    Tenancy,
    form=TenancyForm,
    formset=BaseTenancyInlineFormSet,
    extra=2
)


class WalletAddressForm(forms.ModelForm):
    class Meta:
        model = WalletAddress
        exclude = ["contact"]

    def __init__(self, *args, **kwargs):
        """
        Set the empty_label for the Network field.
        """
        super(WalletAddressForm, self).__init__(*args, **kwargs)
        self.fields["network"].empty_label = "-- Select Network --"


class BaseWalletAddressInlineFormSet(SaveFormSetIfNotEmptyMixin, forms.BaseInlineFormSet):
    pass


WalletAddressFormSet = forms.inlineformset_factory(
    Contact,
    WalletAddress,
    form=WalletAddressForm,
    formset=BaseWalletAddressInlineFormSet,
    extra=1
)