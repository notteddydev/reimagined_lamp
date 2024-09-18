from __future__ import annotations

import phonenumbers

from datetime import date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField
from typing import Any

from . import constants
from .utils import get_years_from_year


class ArchiveableQuerySet(models.QuerySet):
    def archived(self) -> ArchiveableQuerySet:
        """
        Filters the QuerySet to return only models that have been archived.
        """
        return self.filter(archived=True)

    def unarchived(self) -> ArchiveableQuerySet:
        """
        Filters the QuerySet to return only models that have not been archived.
        """
        return self.filter(archived=False)


class ArchiveableManager(models.Manager):
    def get_queryset(self) -> ArchiveableQuerySet:
        """
        Returns a custom QuerySet instance for the model managed by this manager.
        """
        return ArchiveableQuerySet(self.model, using=self._db)

    def archived(self) -> ArchiveableQuerySet:
        """
        Filters the QuerySet to return only models that have been archived.
        """
        return self.get_queryset().archived()

    def unarchived(self) -> ArchiveableQuerySet:
        """
        Filters the QuerySet to return only models that have not been archived.
        """
        return self.get_queryset().unarchived()


class Archiveable(models.Model):
    class Meta:
        abstract = True
        ordering = ["archived"]

    objects = ArchiveableManager()

    archived = models.BooleanField(default=False, null=False)


class ContactableTypeQuerySet(models.QuerySet):
    def preferred(self) -> ContactableTypeQuerySet:
        """
        Filters the QuerySet to return only ContactableTypes of the 'preferred' type -
        there should only be one.
        """
        model_name = self.model._meta.object_name
        const_name = f"{model_name.upper()}__NAME_PREF"
        pref = getattr(constants, const_name)
        return self.filter(name=pref)

    def unpreferred(self) -> ContactableTypeQuerySet:
        """
        Filters the QuerySet to return all ContactableTypes not of the 'preferred' type.
        """
        model_name = self.model._meta.object_name
        const_name = f"{model_name.upper()}__NAME_PREF"
        pref = getattr(constants, const_name)
        return self.exclude(name=pref)


class ContactableTypeManager(models.Manager):
    def get_queryset(self) -> ContactableTypeQuerySet:
        """
        Returns a custom QuerySet instance for the model managed by this manager.
        """
        return ContactableTypeQuerySet(self.model, using=self._db)

    def preferred(self) -> ContactableTypeQuerySet:
        """
        Filters the QuerySet to return only ContactableTypes of the 'preferred' type -
        there should only be one.
        """
        return self.get_queryset().preferred()

    def unpreferred(self) -> ContactableTypeQuerySet:
        """
        Filters the QuerySet to return all ContactableTypes not of the 'preferred' type.
        """
        return self.get_queryset().unpreferred()


class ContactableType(models.Model):
    class Meta:
        abstract = True
        ordering = ["verbose"]

    objects = ContactableTypeManager()

    name = models.CharField(max_length=9)
    verbose = models.CharField(max_length=15)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return self.verbose


class ContactableQuerySet(models.QuerySet):
    def preferred(self) -> ContactableQuerySet:
        """
        Filters the QuerySet to return only Contactables associated with the 'preferred'
        ContactableType - there should be a maximum of one.
        """
        model_name = self.model._meta.object_name
        field_name = f"{model_name.lower()}_types"
        field = self.model._meta.get_field(field_name)
        subquery = field.related_model.objects.preferred().values("id")
        qkwargs = {f"{field_name}__in": models.Subquery(subquery)}
        return self.filter(**qkwargs)

    def unpreferred(self) -> ContactableQuerySet:
        """
        Filters the QuerySet to return only Contactables not associated with the 'preferred'
        ContactableType.
        """
        model_name = self.model._meta.object_name
        field_name = f"{model_name.lower()}_types"
        field = self.model._meta.get_field(field_name)
        subquery = field.related_model.objects.preferred().values("id")
        qkwargs = {f"{field_name}__in": models.Subquery(subquery)}
        return self.exclude(**qkwargs)


class ContactableManager(models.Manager):
    def get_queryset(self) -> ContactableQuerySet:
        """
        Returns a custom QuerySet instance for the model managed by this manager.
        """
        return ContactableQuerySet(self.model, using=self._db)

    def preferred(self) -> ContactableQuerySet:
        """
        Filters the QuerySet to return only Contactables associated with the 'preferred'
        ContactableType - there should be a maximum of one.
        """
        return self.get_queryset().preferred()

    def unpreferred(self) -> ContactableQuerySet:
        """
        Filters the QuerySet to return only Contactables not associated with the 'preferred'
        ContactableType.
        """
        return self.get_queryset().unpreferred()


class ArchiveableContactableQuerySet(ArchiveableQuerySet, ContactableQuerySet, models.QuerySet):
    pass


class ArchiveableContactableManager(models.Manager):
    def get_queryset(self) -> ArchiveableContactableQuerySet:
        """
        Returns a custom QuerySet instance for the model managed by this manager.
        """
        return ArchiveableContactableQuerySet(self.model, using=self._db)

    def archived(self) -> ArchiveableContactableQuerySet:
        """
        Filters the QuerySet to return only models that have been archived.
        """
        return self.get_queryset().archived()

    def preferred(self) -> ArchiveableContactableQuerySet:
        """
        Filters the QuerySet to return only Contactables associated with the 'preferred'
        ContactableType - there should be a maximum of one.
        """
        return self.get_queryset().preferred()

    def unarchived(self) -> ArchiveableContactableQuerySet:
        """
        Filters the QuerySet to return only models that have not been archived.
        """
        return self.get_queryset().unarchived()

    def unpreferred(self) -> ArchiveableContactableQuerySet:
        """
        Filters the QuerySet to return only Contactables not associated with the 'preferred'
        ContactableType.
        """
        return self.get_queryset().unpreferred()


class Contactable(models.Model):
    class Meta:
        abstract = True

    objects = ContactableManager()

    @property
    def contactable_types(self) -> models.Manager:
        """
        Return the ManyRelatedManager for the ContactableTypes in a commonly named property.
        """
        return getattr(self, f"{self._meta.object_name.lower()}_types")

    @property
    def readable_types(self) -> str:
        """
        Return the ContactableTypes in a comma-separated readable format.
        """
        return ", ".join(self.contactable_types.values_list("verbose", flat=True))

    @property
    def types_for_vcard(self) -> str:
        """
        Return the ContactableTypes comma-separated ready for a vcard.
        """
        return ",".join(self.contactable_types.values_list("name", flat=True))


class Nation(models.Model):
    class Meta:
        ordering = ["verbose"]

    code = models.CharField(blank=False, max_length=3)
    verbose = models.CharField(blank=False, max_length=52)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return self.verbose


class Tag(models.Model):
    class Meta:
        ordering = ["name"]
        unique_together = ("name", "user",)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return self.name


class Tenancy(Archiveable, Contactable, models.Model):
    class Meta(Archiveable.Meta):
        unique_together = ("contact", "address",)

    objects = ArchiveableContactableManager()

    contact = models.ForeignKey("Contact", on_delete=models.CASCADE)
    address = models.ForeignKey("Address", on_delete=models.CASCADE)
    tenancy_types = models.ManyToManyField("AddressType")

    @property
    def vcard_entry(self) -> str:
        """
        Prepares an Address entry for a vcard for the Tenancy and associated Address to be included
        in a .vcf file for a Contact.
        """
        adr = f"ADR;TYPE={self.types_for_vcard}:"
        adr += f"{self.address.address_line_1};{self.address.address_line_2};"
        if self.address.neighbourhood:
            adr += f"{self.address.neighbourhood}, "

        return f"{adr}{self.address.city};{self.address.state};{self.address.postcode};{self.address.country.verbose}"
    
    def __str__(self) -> str:
        """
        Return the __str__ of the associated contact and address.
        """
        return f"{self.contact} - {self.address}"


class Contact(models.Model):
    class Meta:
        ordering = ["first_name"]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(blank=False, max_length=100)
    middle_names = models.CharField(blank=True, max_length=200)
    last_name = models.CharField(blank=True, max_length=100)
    nickname = models.CharField(blank=True, max_length=50)
    gender = models.CharField(
        choices=[
            (None, "-- Select Gender --"),
            (constants.CONTACT_GENDER_MALE, "Male"),
            (constants.CONTACT_GENDER_FEMALE, "Female"),
        ],
        max_length=1,
    )
    dob = models.DateField(blank=True, null=True)
    dod = models.DateField(blank=True, null=True)
    anniversary = models.DateField(blank=True, null=True)
    addresses = models.ManyToManyField("Address", blank=True, through=Tenancy)
    nationalities = models.ManyToManyField(Nation, blank=True)
    year_met = models.SmallIntegerField(
        blank=False,
        choices=[(None, "-- Select Year --")] + [(year, str(year)) for year in get_years_from_year()],
        null=False,
    )
    is_business = models.BooleanField(default=False, null=False)
    tags = models.ManyToManyField(Tag, blank=True, symmetrical=True)
    family_members = models.ManyToManyField("self", blank=True, symmetrical=True)
    profession = models.ForeignKey("Profession", blank=True, on_delete=models.SET_NULL, null=True)
    website = models.CharField(blank=True, max_length=100)
    notes = models.TextField(blank=True)

    @property
    def age(self) -> int | None:
        """
        If the Contact has a dob, returns their calculated age. If not, returns None.
        """
        return relativedelta(date.today(), self.dob).years if self.dob else None

    @property
    def age_passed(self) -> int | None:
        """
        If the Contact has a dob and dod, returns the calculated age at which they passed. If not, returns None.
        """
        return relativedelta(self.dod, self.dob).years if self.dob and self.dod else None

    @property
    def known_for_years(self) -> str:
        """
        Returns a string providing the two possible calculations for the number of years the User has known
        the Contact for, separated by a forward slash.
        """
        higher = date.today().year - self.year_met
        return f"{higher - 1}/{higher}"

    @property
    def full_name(self) -> str:
        """
        Concatenates the first_name, middle_names, and last_name field values, only if they are not empty strings.
        """
        full_name = self.first_name

        if len(self.middle_names):
            full_name += f" {self.middle_names}"

        if len(self.last_name):
            full_name += f" {self.last_name}"

        return full_name

    @property
    def vcard(self) -> str:
        """
        Returns the vcard string for the Contact, containing all non-archived contact data for them, ready to be
        downloaded as a .vcf file.
        """
        vcard = f"""
        BEGIN:VCARD
        VERSION:3.0
        CATEGORIES:{", ".join(self.tags.values_list("name", flat=True))}
        FN:{self.full_name}
        GENDER:{self.gender.upper()}
        KIND:{"organization" if self.is_business else "individual"}
        N:{self.last_name};{self.first_name};{self.middle_names};;
        NICKNAME:{self.nickname}
        NOTE:{self.notes}
        TITLE:{self.profession}
        URL:{self.website}
        """

        if self.anniversary:
            vcard += f"""ANNIVERSARY:{self.anniversary.strftime("%Y%m%d")}\n"""

        if self.dob:
            vcard += f"""BDAY:{self.dob.strftime("%Y%m%d")}\n"""

        for tenancy in self.tenancy_set.unarchived():
            vcard += f"{tenancy.vcard_entry}\n"

            for phonenumber in tenancy.address.phonenumber_set.unarchived():
                vcard += f"{phonenumber.vcard_entry}\n"

        for email in self.email_set.unarchived():
            vcard += f"{email.vcard_entry}\n"

        for phonenumber in self.phonenumber_set.unarchived():
            vcard += f"{phonenumber.vcard_entry}\n"

        vcard += """END:VCARD"""
        vcard = "\n".join(line.strip() for line in vcard.strip().split("\n"))

        return vcard

    @property
    def years_married(self) -> int | None:
        """
        If the Contact has an anniversary date set, this property returns the number of years for which they have been
        married. If there is no anniversary date set, this returns None.
        """
        return relativedelta(date.today(), self.anniversary).years if self.anniversary else None

    def clean(self) -> None:
        """
        Validate that the Contact is in an acceptable state to be saved to db. Validates cohesion of dates.
        """
        super().clean()
        errors = {
            "anniversary": [],
            "dob": [],
            "dod": [],
            "year_met": [],
        }

        if self.dob:
            if self.anniversary and self.anniversary <= self.dob:
                errors["anniversary"].append("Anniversary must be greater than the date of birth.")
            if self.dob > date.today():
                errors["dob"].append("Date of birth may not be set to a future date.")
            if self.year_met and self.dob.year > self.year_met:
                errors["year_met"].append("Year met may not be before the date of birth.")
        if self.dod:
            if self.anniversary and self.anniversary > self.dod:
                errors["anniversary"].append("Anniversary must be sooner than the date of passing.")
            if self.dob and self.dob > self.dod:
                errors["dob"].append("Date of birth may not be after date of passing.")
            if self.dod > date.today():
                errors["dod"].append("Date of passing may not be set to a future date.")
            if self.year_met and self.dod.year < self.year_met:
                errors["year_met"].append("Year met may not be after date of passing.")
        if self.year_met and self.year_met not in dict(self._meta.get_field("year_met").choices):
            errors["year_met"].append(f"Select a valid choice. {self.year_met} is not one of the available choices.")

        errors = {field: errorlist for field, errorlist in errors.items() if errorlist}

        if errors:
            raise ValidationError(errors)

    def get_absolute_url(self) -> str:
        """
        Returns the canonical URL for this instance of Contact.
        """
        return reverse("contact-detail", args=[self.id])

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override the models save method, to ensure that clean() is called to validate it before saving to db.
        """
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return f"{self.first_name} {self.last_name}"


class PhoneNumberType(ContactableType, models.Model):
    pass


class PhoneNumber(Archiveable, Contactable, models.Model):
    objects = ArchiveableContactableManager()

    number = PhoneNumberField(null=False)
    address = models.ForeignKey("Address", on_delete=models.CASCADE, null=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    phonenumber_types = models.ManyToManyField(PhoneNumberType)

    @property
    def country_code(self) -> str:
        """
        The two letter alphabetic string representing the country to which the PhoneNumber belongs.
        Click through for more.
        """
        return phonenumbers.region_code_for_country_code(self.country_prefix)

    @property
    def country_prefix(self) -> int | None:
        """
        The PhoneNumber international prefix required for calling internationally e.g. +1 for USA.
        """
        return self.parsed.country_code

    @property
    def formatted(self) -> str:
        """
        The formatted PhoneNumber, for easier reading.
        """
        return phonenumbers.format_number(self.parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    @property
    def national_number(self) -> int | None:
        """
        The PhoneNumber, without preceeding 'country_prefix'.
        """
        return self.parsed.national_number

    @property
    def parsed(self) -> phonenumbers.PhoneNumber:
        """
        Returns the 'parsed' PhoneNumber, as a PhoneNumber (not address_book.model) object for accessing the
        country_code and national_number.
        """
        return phonenumbers.parse(str(self.number))

    @property
    def vcard_entry(self) -> str:
        """
        Prepares a PhoneNumber entry for a vcard to be included in a .vcf file for a Contact.
        """
        return f"TEL;TYPE={self.types_for_vcard}:{self.number}"
    
    def __str__(self) -> str:
        """
        Return the formatted PhoneNumber.
        """
        return self.formatted


class AddressType(ContactableType, models.Model):
    pass


class Address(models.Model):
    class Meta:
        ordering = ["country__verbose", "city", "address_line_1"]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    neighbourhood = models.CharField(blank=True, max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(blank=True, max_length=100)
    postcode = models.CharField(blank=True, max_length=20)
    country = models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)

    @property
    def readable(self) -> str:
        """
        Returns the Address model as a readable string, with linebreaks as if it were written on an envelope.
        """
        readable = ""
        address_parts = (self.address_line_1, self.address_line_2,
                         self.neighbourhood, self.city, self.state, self.postcode)

        for address_part in address_parts:
            if len(address_part):
                readable += f"{address_part}\n"

        if self.country:
            readable += f"{self.country.verbose}\n"

        if self.notes:
            readable += f"\nNotes:\n{self.notes}"

        return readable

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return f"{self.address_line_1} {self.city}"


class EmailType(ContactableType, models.Model):
    pass


class Email(Archiveable, Contactable, models.Model):
    objects = ArchiveableContactableManager()

    email = models.EmailField(unique=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    email_types = models.ManyToManyField(EmailType)

    @property
    def vcard_entry(self) -> str:
        """
        Prepares an Email entry for a vcard to be included in a .vcf file for a Contact.
        """
        return f"EMAIL;TYPE=INTERNET,{self.types_for_vcard}:{self.email}"
    
    def __str__(self) -> str:
        """
        Return the email address.
        """
        return self.email


class CryptoNetwork(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return f"{self.name} ({self.symbol})"


class WalletAddress(Archiveable, models.Model):
    TRANSMISSION_CHOICES = [
        (None, "-- Select Transmission --"),
        (constants.WALLETADDRESS_TRANSMISSION_THEY_RECEIVE, "They receive to this address",),
        (constants.WALLETADDRESS_TRANSMISSION_YOU_RECEIVE, "You receive from this address",)
    ]

    network = models.ForeignKey(CryptoNetwork, on_delete=models.CASCADE)
    transmission = models.CharField(blank=False, choices=TRANSMISSION_CHOICES, max_length=12)
    address = models.CharField(blank=False, max_length=96)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)

    @property
    def transmission_hr(self) -> str:
        """
        Returns the transmission property in a human readable format.
        """
        return " ".join(self.transmission.split("_")).capitalize()
    
    def __str__(self) -> str:
        """
        Return the human-readable transmission property, symbol, and address.
        """
        return f"({self.transmission_hr}) {self.network.symbol}: {self.address}"


class Profession(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        """
        Returns a human-readable string representation of the object.
        """
        return self.name
