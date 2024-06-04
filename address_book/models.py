from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

class Nation(models.Model):
    code=models.CharField(blank=False, max_length=3)
    verbose=models.CharField(blank=False, max_length=50)

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
    met_through_contact=models.OneToOneField("self", blank=True, on_delete=models.SET_NULL, null=True)
    family_members=models.ManyToManyField("self", blank=True, symmetrical=True)
    profession=models.CharField(blank=True, max_length=50)
    website=models.CharField(blank=True, max_length=100)
    dod=models.DateField(blank=True, null=True)
    middle_names=models.CharField(blank=True, max_length=200)
    notes=models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse("contact-detail", args=[self.id])
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class PhoneNumber(models.Model):
    country_code=models.PositiveSmallIntegerField(null=False, validators=[MaxValueValidator(999), MinValueValidator(1)])
    number=models.PositiveIntegerField(null=False)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)

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
    email=models.EmailField(primary_key=True)
    contact=models.ForeignKey(Contact, on_delete=models.CASCADE)

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
