# Generated by Django 5.0.6 on 2024-07-11 09:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('address_book', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contactaddress',
            unique_together={('contact', 'address')},
        ),
    ]