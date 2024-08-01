# Generated by Django 5.0.6 on 2024-08-01 13:34

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
                ('name', models.CharField(max_length=9)),
                ('verbose', models.CharField(max_length=15)),
            ],
            options={
                'abstract': False,
            },
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
            name='EmailType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=9)),
                ('verbose', models.CharField(max_length=15)),
            ],
            options={
                'abstract': False,
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
            name='PhoneNumberType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=9)),
                ('verbose', models.CharField(max_length=15)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Profession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
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
                ('website', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('family_members', models.ManyToManyField(blank=True, to='address_book.contact')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('nationality', models.ManyToManyField(blank=True, to='address_book.nation')),
                ('profession', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='address_book.profession')),
            ],
            options={
                'ordering': ['first_name'],
            },
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
                ('email_types', models.ManyToManyField(to='address_book.emailtype')),
            ],
            options={
                'ordering': ['archived'],
                'abstract': False,
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
                ('address_types', models.ManyToManyField(to='address_book.addresstype')),
                ('country', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='address_book.nation')),
            ],
            options={
                'ordering': ['country__verbose', 'city', 'address_line_1'],
            },
        ),
        migrations.CreateModel(
            name='PhoneNumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('number', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None)),
                ('address', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='address_book.address')),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
                ('phonenumber_types', models.ManyToManyField(to='address_book.phonenumbertype')),
            ],
            options={
                'ordering': ['archived'],
                'abstract': False,
            },
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
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archived', models.BooleanField(default=False)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.address')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='address_book.contact')),
            ],
            options={
                'ordering': ['archived'],
                'abstract': False,
                'unique_together': {('contact', 'address')},
            },
        ),
        migrations.AddField(
            model_name='contact',
            name='addresses',
            field=models.ManyToManyField(blank=True, through='address_book.Tenant', to='address_book.address'),
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
