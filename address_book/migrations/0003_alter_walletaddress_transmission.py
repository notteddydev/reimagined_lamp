# Generated by Django 5.0.6 on 2024-06-27 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('address_book', '0002_alter_contact_options_alter_nation_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='walletaddress',
            name='transmission',
            field=models.CharField(choices=[('they_receive', 'They receive to this address'), ('you_receive', 'You receive from this address')], max_length=12),
        ),
    ]