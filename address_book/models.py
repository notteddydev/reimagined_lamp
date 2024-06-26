from datetime import date
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from phonenumber_field.modelfields import PhoneNumberField

class Nation(models.Model):
    code=models.CharField(blank=False, max_length=3)
    verbose=models.CharField(blank=False, max_length=50)

    def __str__(self):
        return self.verbose

class Tag(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    name=models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Contact(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    nickname=models.CharField(blank=True, max_length=50)
    first_name=models.CharField(blank=False, max_length=100)
    last_name=models.CharField(blank=True, max_length=100)
    dob=models.DateField(blank=True, null=True)
    addresses=models.ManyToManyField("Address", blank=True)
    nationality=models.ManyToManyField(Nation, blank=True)
    year_met=models.SmallIntegerField(blank=False, null=False)
    is_business=models.BooleanField(default=False, null=False)
    tags=models.ManyToManyField(Tag, blank=True, symmetrical=True)
    family_members=models.ManyToManyField("self", blank=True, symmetrical=True)
    profession=models.CharField(blank=True, max_length=50)
    website=models.CharField(blank=True, max_length=100)
    dod=models.DateField(blank=True, null=True)
    middle_names=models.CharField(blank=True, max_length=200)
    notes=models.TextField(blank=True)

    @property
    def age(self):
        if not self.dob:
            return None
        
        return relativedelta(date.today(), self.dob).years
    
    @property
    def age_passed(self):
        if not self.dod:
            return None
        
        return relativedelta(self.dod, self.dob).years
    
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

    def get_absolute_url(self):
        return reverse("contact-detail", args=[self.id])
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class PhoneNumber(models.Model):
    number=PhoneNumberField(null=False)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE, null=True)
    
    @property
    def sms_href(self):
        return f"sms:{self.number}"

    @property
    def tel_href(self):
        return f"tel:{self.number}"
    
    @property
    def wa_href(self):
        return f"https://wa.me/{self.number}"

class Address(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1=models.CharField(max_length=100)
    address_line_2=models.CharField(max_length=100)
    postcode=models.CharField(max_length=20)
    neighbourhood=models.CharField(max_length=100)
    state=models.CharField(max_length=100)
    country=models.ForeignKey(Nation, on_delete=models.SET_NULL, null=True)
    notes=models.TextField(blank=True)
    landline=models.OneToOneField(PhoneNumber, on_delete=models.SET_NULL, null=True)

class Email(models.Model):
    email=models.EmailField(unique=True)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)

    @property
    def href(self):
        return f"mailto:{self.email}"

class WalletAddress(models.Model):
    TRANSMISSION_SENDING = "They receive to this address"
    TRANSMISSION_RECEIVING = "You receive from this address"
    TRANSMISSION_CHOICES = [
        (TRANSMISSION_SENDING, TRANSMISSION_SENDING,),
        (TRANSMISSION_RECEIVING, TRANSMISSION_RECEIVING,)
    ]

    network=models.CharField(max_length=50)
    transmission=models.CharField(blank=False, choices=TRANSMISSION_CHOICES, max_length=30)
    address=models.CharField(blank=False, max_length=96)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)