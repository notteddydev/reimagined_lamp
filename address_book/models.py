from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from phonenumber_field.modelfields import PhoneNumberField

from . import constants


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


class ContactableType(models.Model):
    name=models.CharField(max_length=9)
    verbose=models.CharField(max_length=15)

    def __str__(self):
        return self.verbose

    class Meta:
        abstract = True
    

class PreferableQuerySet(models.QuerySet):
    def preferred(self):
        model_name = self.model._meta.object_name
        name_field = f"{model_name.lower()}_types__name"
        pref_name = getattr(constants, f"{model_name.upper()}_TYPE__NAME_PREF")
        
        return self.filter(**{name_field: pref_name})


class PreferableManager(ArchiveableManager):
    def get_queryset(self):
        return PreferableQuerySet(self.model, using=self._db)
    
    def preferred(self):
        return self.get_queryset().preferred()


class Contactable(models.Model):
    objects = PreferableManager()

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
    name=models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Tenant(Archiveable):
    contact=models.ForeignKey("Contact", on_delete=models.CASCADE)
    address=models.ForeignKey("Address", on_delete=models.CASCADE)

    class Meta(Archiveable.Meta):
        unique_together = ("contact", "address")
        

class Contact(models.Model):
    YEAR_MET_CHOICES = list(map(lambda year: (year, str(year)), range(1996, datetime.now().year + 1)[::-1]))

    user=models.ForeignKey(User, on_delete=models.CASCADE)
    first_name=models.CharField(blank=False, max_length=100)
    middle_names=models.CharField(blank=True, max_length=200)
    last_name=models.CharField(blank=True, max_length=100)
    nickname=models.CharField(blank=True, max_length=50)
    gender=models.CharField(
        choices=[(None, "-- Select Gender --"), ("m", "Male"), ("f", "Female")],
        max_length=1,
    )
    dob=models.DateField(blank=True, null=True)
    dod=models.DateField(blank=True, null=True)
    anniversary=models.DateField(blank=True, null=True)
    addresses=models.ManyToManyField("Address", blank=True, through=Tenant)
    nationality=models.ManyToManyField(Nation, blank=True)
    year_met=models.SmallIntegerField(
        blank=False,
        choices=[(None, "-- Select Year --")] + YEAR_MET_CHOICES,
        null=False,
    )
    is_business=models.BooleanField(default=False, null=False)
    tags=models.ManyToManyField(Tag, blank=True, symmetrical=True)
    family_members=models.ManyToManyField("self", blank=True, symmetrical=True)
    profession=models.ForeignKey("Profession", on_delete=models.SET_NULL, null=True)
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
        return date.today().year - self.year_met

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

        for tenant in self.tenant_set.unarchived():
            vcard += f"{tenant.address.vcard_entry}\n"

            for phonenumber in tenant.address.phonenumber_set.unarchived():
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

    def get_absolute_url(self):
        return reverse("contact-detail", args=[self.id])
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["first_name"]


class PhoneNumberType(ContactableType):
    pass
    

class PhoneNumber(Archiveable, Contactable):
    number=PhoneNumberField(null=False)
    address=models.ForeignKey("Address", on_delete=models.CASCADE, null=True)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    phonenumber_types=models.ManyToManyField(PhoneNumberType)
    
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
    

class AddressType(ContactableType):
    pass


class Address(Contactable):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1=models.CharField(max_length=100)
    address_line_2=models.CharField(blank=True, max_length=100)
    neighbourhood=models.CharField(blank=True, max_length=100)
    city=models.CharField(max_length=100)
    state=models.CharField(blank=True, max_length=100)
    postcode=models.CharField(max_length=20)
    country=models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True)
    notes=models.TextField(blank=True)
    address_types=models.ManyToManyField(AddressType)

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
    
    @property
    def vcard_entry(self):
        adr = f"ADR;TYPE={self.types_for_vcard}:"
        adr += f"{self.address_line_1};{self.address_line_2};"
        if self.neighbourhood:
            adr += f"{self.neighbourhood}, "
            
        return f"{adr}{self.city};{self.state};{self.postcode};{self.country.verbose}"
    
    def __str__(self):
        return f"{self.address_line_1} {self.city}"
    
    class Meta:
        ordering = ["country__verbose", "city", "address_line_1"]
    

class EmailType(ContactableType):
    pass


class Email(Archiveable, Contactable):
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
    symbol=models.CharField(max_length=3, unique=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

    class Meta:
        ordering = ["name"]


class WalletAddress(Archiveable):
    TRANSMISSION_CHOICES = [
        (None, "-- Select Transmission --"),
        ("they_receive", "They receive to this address",),
        ("you_receive", "You receive from this address",)
    ]

    network=models.ForeignKey(CryptoNetwork, on_delete=models.CASCADE)
    transmission=models.CharField(blank=False, choices=TRANSMISSION_CHOICES, max_length=12)
    address=models.CharField(blank=False, max_length=96)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)

    @property
    def transmission_hr(self):
        return " ".join(self.transmission.split('_')).capitalize()


class Profession(models.Model):
    name=models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]
