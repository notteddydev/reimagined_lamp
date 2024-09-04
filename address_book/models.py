from datetime import date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from phonenumber_field.modelfields import PhoneNumberField
import phonenumbers

from . import constants
from .utils import get_years_from_year


class ArchiveableQuerySet(models.QuerySet):
    def archived(self):
        return self.filter(archived=True)
    
    def unarchived(self):
        return self.filter(archived=False)
    

class ArchiveableManager(models.Manager):
    def get_queryset(self):
        return ArchiveableQuerySet(self.model, using=self._db)

    def archived(self):
        return self.get_queryset().archived()

    def unarchived(self):
        return self.get_queryset().unarchived()
    

class Archiveable(models.Model):
    archived = models.BooleanField(default=False, null=False)

    objects = ArchiveableManager()

    class Meta:
        abstract = True
        ordering = ["archived"]
    

class ContactableTypeQuerySet(models.QuerySet):
    def preferred(self):
        model_name = self.model._meta.object_name
        const_name = f"{model_name.upper()}__NAME_PREF"
        pref = getattr(constants, const_name)
        return self.filter(name=pref)
    
    def unpreferred(self):
        model_name = self.model._meta.object_name
        const_name = f"{model_name.upper()}__NAME_PREF"
        pref = getattr(constants, const_name)
        return self.exclude(name=pref)


class ContactableTypeManager(models.Manager):
    def get_queryset(self):
        return ContactableTypeQuerySet(self.model, using=self._db)
    
    def preferred(self):
        return self.get_queryset().preferred()
    
    def unpreferred(self):
        return self.get_queryset().unpreferred()


class ContactableType(models.Model):
    objects = ContactableTypeManager()

    name=models.CharField(max_length=9)
    verbose=models.CharField(max_length=15)

    def __str__(self):
        return self.verbose

    class Meta:
        abstract = True
        ordering = ["verbose"]
    

class ContactableQuerySet(models.QuerySet):
    def preferred(self):
        model_name = self.model._meta.object_name
        field_name = f"{model_name.lower()}_types"
        field = self.model._meta.get_field(field_name)
        subquery = field.related_model.objects.preferred().values("id")
        qkwargs = {f"{field_name}__in": models.Subquery(subquery)}
        return self.filter(**qkwargs)
    
    def unpreferred(self):
        model_name = self.model._meta.object_name
        field_name = f"{model_name.lower()}_types"
        field = self.model._meta.get_field(field_name)
        subquery = field.related_model.objects.preferred().values("id")
        qkwargs = {f"{field_name}__in": models.Subquery(subquery)}
        return self.exclude(**qkwargs)


class ContactableManager(models.Manager):
    def get_queryset(self):
        return ContactableQuerySet(self.model, using=self._db)
    
    def preferred(self):
        return self.get_queryset().preferred()
    
    def unpreferred(self):
        return self.get_queryset().unpreferred()


class ArchiveableContactableQuerySet(ArchiveableQuerySet, ContactableQuerySet, models.QuerySet):
    pass


class ArchiveableContactableManager(models.Manager):
    def get_queryset(self):
        return ArchiveableContactableQuerySet(self.model, using=self._db)

    def archived(self):
        return self.get_queryset().archived()

    def preferred(self):
        return self.get_queryset().preferred()
    
    def unarchived(self):
        return self.get_queryset().unarchived()
    
    def unpreferred(self):
        return self.get_queryset().unpreferred()


class Contactable(models.Model):
    objects = ContactableManager()

    @property
    def contactable_types(self):
        return getattr(self, f"{self._meta.object_name.lower()}_types")
    
    @property
    def readable_types(self):
        return ", ".join(self.contactable_types.values_list("verbose", flat=True))

    @property
    def types_for_vcard(self):
        return ",".join(self.contactable_types.values_list("name", flat=True))

    class Meta:
        abstract = True


class Nation(models.Model):
    code=models.CharField(blank=False, max_length=3)
    verbose=models.CharField(blank=False, max_length=52)

    def __str__(self):
        return self.verbose

    class Meta:
        ordering = ["verbose"]


class Tag(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    name=models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "user",)


class Tenancy(Archiveable, Contactable, models.Model):
    objects = ArchiveableContactableManager()

    contact=models.ForeignKey("Contact", on_delete=models.CASCADE)
    address=models.ForeignKey("Address", on_delete=models.CASCADE)
    tenancy_types=models.ManyToManyField("AddressType")
    
    @property
    def vcard_entry(self):
        adr = f"ADR;TYPE={self.types_for_vcard}:"
        adr += f"{self.address.address_line_1};{self.address.address_line_2};"
        if self.address.neighbourhood:
            adr += f"{self.address.neighbourhood}, "
            
        return f"{adr}{self.address.city};{self.address.state};{self.address.postcode};{self.address.country.verbose}"

    class Meta(Archiveable.Meta):
        unique_together = ("contact", "address",)
        

class Contact(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    first_name=models.CharField(blank=False, max_length=100)
    middle_names=models.CharField(blank=True, max_length=200)
    last_name=models.CharField(blank=True, max_length=100)
    nickname=models.CharField(blank=True, max_length=50)
    gender=models.CharField(
        choices=[(None, "-- Select Gender --"), (constants.CONTACT_GENDER_MALE, "Male"), (constants.CONTACT_GENDER_FEMALE, "Female")],
        max_length=1,
    )
    dob=models.DateField(blank=True, null=True)
    dod=models.DateField(blank=True, null=True)
    anniversary=models.DateField(blank=True, null=True)
    addresses=models.ManyToManyField("Address", blank=True, through=Tenancy)
    nationalities=models.ManyToManyField(Nation, blank=True)
    year_met=models.SmallIntegerField(
        blank=False,
        choices=[(None, "-- Select Year --")] + [(year, str(year)) for year in get_years_from_year()],
        null=False,
    )
    is_business=models.BooleanField(default=False, null=False)
    tags=models.ManyToManyField(Tag, blank=True, symmetrical=True)
    family_members=models.ManyToManyField("self", blank=True, symmetrical=True)
    profession=models.ForeignKey("Profession", blank=True, on_delete=models.SET_NULL, null=True)
    website=models.CharField(blank=True, max_length=100)
    notes=models.TextField(blank=True)

    @property
    def age(self):
        return relativedelta(date.today(), self.dob).years if self.dob else None
    
    @property
    def age_passed(self):
        return relativedelta(self.dod, self.dob).years if self.dod else None
    
    @property
    def known_for_years(self):
        higher = date.today().year - self.year_met
        return f"{higher - 1}/{higher}"

    @property
    def full_name(self):
        full_name = self.first_name

        if len(self.middle_names):
            full_name += f" {self.middle_names}"

        if len(self.last_name):
            full_name += f" {self.last_name}"

        return full_name
    
    @property
    def vcard(self):
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
    def years_married(self):
        return relativedelta(date.today(), self.anniversary).years if self.anniversary else None
    
    def clean(self) -> None:
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

    def get_absolute_url(self):
        return reverse("contact-detail", args=[self.id])
    
    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name"]


class PhoneNumberType(ContactableType, models.Model):
    pass
    

class PhoneNumber(Archiveable, Contactable, models.Model):
    objects = ArchiveableContactableManager()

    number=PhoneNumberField(null=False)
    address=models.ForeignKey("Address", on_delete=models.CASCADE, null=True)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    phonenumber_types=models.ManyToManyField(PhoneNumberType)

    @property
    def country_code(self):
        return phonenumbers.region_code_for_country_code(self.country_prefix)

    @property
    def country_prefix(self):
        return self.parsed.country_code
    
    @property
    def formatted(self):
        return phonenumbers.format_number(self.parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    
    @property
    def national_number(self):
        return self.parsed.national_number
    
    @property
    def parsed(self):
        return phonenumbers.parse(str(self.number))
    
    @property
    def sms_href(self):
        return f"sms:{self.number}"

    @property
    def tel_href(self):
        return f"tel:{self.number}"
    
    @property
    def vcard_entry(self):
        return f"TEL;TYPE={self.types_for_vcard}:{self.number}"
    
    @property
    def wa_href(self):
        return f"https://wa.me/{self.number}"
    

class AddressType(ContactableType, models.Model):
    pass


class Address(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1=models.CharField(blank=True, max_length=100)
    address_line_2=models.CharField(blank=True, max_length=100)
    neighbourhood=models.CharField(blank=True, max_length=100)
    city=models.CharField(max_length=100)
    state=models.CharField(blank=True, max_length=100)
    postcode=models.CharField(blank=True, max_length=20)
    country=models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True)
    notes=models.TextField(blank=True)

    @property
    def readable(self):
        readable = ""
        address_parts = (self.address_line_1, self.address_line_2, self.neighbourhood, self.city, self.state, self.postcode)

        for address_part in address_parts:
            if len(address_part):
                readable += f"{address_part}\n"

        if self.country:
            readable += f"{self.country.verbose}\n"

        if self.notes:
            readable += f"\nNotes:\n{self.notes}"

        return readable
    
    def __str__(self):
        return f"{self.address_line_1} {self.city}"
    
    class Meta:
        ordering = ["country__verbose", "city", "address_line_1"]
    

class EmailType(ContactableType, models.Model):
    pass


class Email(Archiveable, Contactable, models.Model):
    objects = ArchiveableContactableManager()

    email=models.EmailField(unique=True)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)
    email_types=models.ManyToManyField(EmailType)

    @property
    def href(self):
        return f"mailto:{self.email}"
    
    @property
    def vcard_entry(self):
        return f"EMAIL;TYPE=INTERNET,{self.types_for_vcard}:{self.email}"


class CryptoNetwork(models.Model):
    name=models.CharField(max_length=100, unique=True)
    symbol=models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    class Meta:
        ordering = ["name"]


class WalletAddress(Archiveable, models.Model):
    TRANSMISSION_CHOICES = [
        (None, "-- Select Transmission --"),
        (constants.WALLETADDRESS_TRANSMISSION_THEY_RECEIVE, "They receive to this address",),
        (constants.WALLETADDRESS_TRANSMISSION_YOU_RECEIVE, "You receive from this address",)
    ]

    network=models.ForeignKey(CryptoNetwork, on_delete=models.CASCADE)
    transmission=models.CharField(blank=False, choices=TRANSMISSION_CHOICES, max_length=12)
    address=models.CharField(blank=False, max_length=96)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)

    @property
    def transmission_hr(self):
        return " ".join(self.transmission.split("_")).capitalize()


class Profession(models.Model):
    name=models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]
