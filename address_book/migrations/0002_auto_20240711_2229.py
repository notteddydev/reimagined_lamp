# Generated by Django 5.0.6 on 2024-07-11 20:52

import csv

from django.conf import settings
from django.db import migrations
from address_book import constants


def insert_address_types(apps, schema_editor):
    AddressType = apps.get_model("address_book", "AddressType")

    address_types = [
        (constants.ADDRESS_TYPE__NAME_HOME, "Home",),
        (constants.ADDRESS_TYPE__NAME_WORK, "Work",),
        (constants.ADDRESS_TYPE__NAME_DOM, "Domestic",),
        (constants.ADDRESS_TYPE__NAME_INTL, "International",),
        (constants.ADDRESS_TYPE__NAME_POSTAL, "Postal",),
        (constants.ADDRESS_TYPE__NAME_PARCEL, "Parcel",),
        (constants.ADDRESS_TYPE__NAME_PREF, "Preferred",),
    ]

    for name, verbose in address_types:
        AddressType.objects.create(name=name, verbose=verbose)

def remove_address_types(apps, schema_editor):
    AddressType = apps.get_model("address_book", "AddressType")

    AddressType.objects.all().delete()


def insert_nations(apps, schema_editor):
    Nation = apps.get_model("address_book", "Nation")

    with open(f"{settings.BASE_DIR}/country_data.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Nation.objects.create(code=row["alpha-3"], verbose=row["name"])

def remove_nations(apps, schema_editor):
    Nation = apps.get_model("address_book", "Nation")

    Nation.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('address_book', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_address_types, remove_address_types),
        migrations.RunPython(insert_nations, remove_nations),
    ]
