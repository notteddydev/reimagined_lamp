# Generated by Django 5.0.6 on 2024-06-26 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address_book', '0005_alter_phonenumber_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phonenumber',
            name='number',
            field=models.IntegerField(),
        ),
    ]