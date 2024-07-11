# Generated by Django 5.0.6 on 2024-07-11 22:29

import django.db.models.deletion
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AddressType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=6)),
                ('verbose', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='CryptoNetwork',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('symbol', models.CharField(max_length=3, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Nation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3)),
                ('verbose', models.CharField(max_length=52)),
            ],
            options={
                'ordering': ['verbose'],
            },
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address_line_1', models.CharField(max_length=100)),
                ('address_line_2', models.CharField(blank=True, max_length=100)),
                ('neighbourhood', models.CharField(blank=True, max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('postcode', models.CharField(max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['country__verbose', 'city', 'address_line_1'],
            },
        ),
        migrations.CreateModel(
            name='AddressAddressType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.address')),
                ('address_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.addresstype')),
            ],
            options={
                'db_table': 'address_book_address_address_types',
                'unique_together': {('address', 'address_type')},
            },
        ),
        migrations.AddField(
            model_name='address',
            name='types',
            field=models.ManyToManyField(through='address_book.AddressAddressType', to='address_book.addresstype'),
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100)),
                ('middle_names', models.CharField(blank=True, max_length=200)),
                ('last_name', models.CharField(blank=True, max_length=100)),
                ('nickname', models.CharField(blank=True, max_length=50)),
                ('gender', models.CharField(choices=[(None, '-- Select Gender --'), ('m', 'Male'), ('f', 'Female')], max_length=1)),
                ('dob', models.DateField(blank=True, null=True)),
                ('dod', models.DateField(blank=True, null=True)),
                ('anniversary', models.DateField(blank=True, null=True)),
                ('year_met', models.SmallIntegerField(choices=[(None, '-- Select Year --'), (2024, '2024'), (2023, '2023'), (2022, '2022'), (2021, '2021'), (2020, '2020'), (2019, '2019'), (2018, '2018'), (2017, '2017'), (2016, '2016'), (2015, '2015'), (2014, '2014'), (2013, '2013'), (2012, '2012'), (2011, '2011'), (2010, '2010'), (2009, '2009'), (2008, '2008'), (2007, '2007'), (2006, '2006'), (2005, '2005'), (2004, '2004'), (2003, '2003'), (2002, '2002'), (2001, '2001'), (2000, '2000'), (1999, '1999'), (1998, '1998'), (1997, '1997'), (1996, '1996')])),
                ('is_business', models.BooleanField(default=False)),
                ('profession', models.CharField(blank=True, max_length=50)),
                ('website', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('family_members', models.ManyToManyField(blank=True, to='address_book.contact')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['first_name'],
            },
        ),
        migrations.CreateModel(
            name='ContactAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.address')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
            ],
            options={
                'db_table': 'address_book_contact_addresses',
                'ordering': ['archived'],
                'abstract': False,
                'unique_together': {('contact', 'address')},
            },
        ),
        migrations.AddField(
            model_name='contact',
            name='addresses',
            field=models.ManyToManyField(blank=True, through='address_book.ContactAddress', to='address_book.address'),
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('type', models.CharField(choices=[(None, '-- Select Type --'), ('HOME', 'Home'), ('WORK', 'Work'), ('PREF', 'Preferred')], max_length=4)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
            ],
            options={
                'ordering': ['archived'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='contact',
            name='nationality',
            field=models.ManyToManyField(blank=True, to='address_book.nation'),
        ),
        migrations.AddField(
            model_name='address',
            name='country',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='address_book.nation'),
        ),
        migrations.CreateModel(
            name='PhoneNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('type', models.CharField(choices=[(None, '-- Select Type --'), ('HOME', 'Home'), ('WORK', 'Work'), ('CELL', 'Mobile'), ('FAX', 'Fax'), ('PAGER', 'Pager'), ('VOICE', 'Voice'), ('VIDEO', 'Video'), ('TEXT', 'Text')], max_length=5)),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
            ],
            options={
                'ordering': ['archived'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='address',
            name='landline',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='address_book.phonenumber'),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='contact',
            name='tags',
            field=models.ManyToManyField(blank=True, to='address_book.tag'),
        ),
        migrations.CreateModel(
            name='WalletAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('transmission', models.CharField(choices=[(None, '-- Select Transmission --'), ('they_receive', 'They receive to this address'), ('you_receive', 'You receive from this address')], max_length=12)),
                ('address', models.CharField(max_length=96)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
                ('network', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.cryptonetwork')),
            ],
            options={
                'ordering': ['archived'],
                'abstract': False,
            },
        ),
    ]
