# Generated by Django 4.2.13 on 2024-06-18 11:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('address_book', '0004_remove_contact_mutual_contacts_tag_contact_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='phonenumber',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='address_book.contact'),
        ),
    ]
