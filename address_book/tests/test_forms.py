import datetime
import random

from collections import Counter
from django import forms
from django.apps import apps
from django.db.models import QuerySet
from django.test import TestCase
from faker import Faker
from typing import List

from address_book import constants
from address_book.factories.address_factories import AddressFactory
from address_book.factories.contact_factories import ContactFactory
from address_book.factories.email_factories import EmailFactory
from address_book.factories.tag_factories import TagFactory
from address_book.factories.user_factories import UserFactory
from address_book.forms import AddressForm, ContactForm, CustomSplitPhoneNumberField, EmailForm, EmailCreateFormSet, EmailUpdateFormSet, PhoneNumberForm, TagForm, TenancyForm, WalletAddressForm
from address_book.models import Address, AddressType, Contact, CryptoNetwork, Email, EmailType, PhoneNumber, PhoneNumberType, Tag, Tenancy, WalletAddress

fake = Faker()


def get_pref_contactable_type_id(contactable_type: str) -> int | None:
    """
    If there is no 'preferred' ContactableType, returns None. Otherwise, returns the ContactableType.id.
    """
    contactable_type = apps.get_model("address_book", contactable_type)
    contactable_type_id = contactable_type.objects.preferred().values_list("id", flat=True).first()

    return contactable_type_id


class BaseFormTestCase:
    def setUp(self) -> None:
        self.other_user = UserFactory.create()
        self.primary_user = UserFactory.create()


class TestAddressForm(BaseFormTestCase, TestCase):
    def test_form_init_with_user(self) -> None:
        """
        Test that the AddressForm is correctly initialised setting the user_id to the form instance.
        """
        form = AddressForm(self.primary_user)

        self.assertEqual(self.primary_user.id, form.instance.user_id)

    def test_form_init_without_user(self) -> None:
        """
        Test that AddressForm instantiation fails when no user is provided to the form instance.
        """
        with self.assertRaises(TypeError) as cm:
            form = AddressForm()
            
        self.assertEqual(str(cm.exception), "AddressForm.__init__() missing 1 required positional argument: 'user'")

    def test_country_field_empty_label(self) -> None:
        """
        Test that the country empty_label is set as desired.
        """
        form = AddressForm(self.primary_user)

        self.assertEqual("-- Select Country --", form.fields["country"].empty_label)

    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = AddressForm(self.primary_user)

        self.assertEqual(
            Counter(["address_line_1", "address_line_2", "city", "country", "neighbourhood", "notes", "postcode", "state"]),
            Counter(form.fields.keys())
        )

    def test_validates_with_only_required_fields(self) -> None:
        """
        Test that the form validates successfully with only the required fields.
        """
        form = AddressForm(self.primary_user, {
            "city": "London",
            "country": 235,
        })
        
        self.assertTrue(form.is_valid())

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = AddressForm(self.primary_user, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["city", "country"]),
            Counter(list(form.errors.as_data()))
        )

    def test_validates_and_saves_with_comprehensive_data(self) -> None:
        """
        Test that the form validates successfully with comprehensive data including the required fields.
        """
        form = AddressForm(self.primary_user, {
            "address_line_1": "1 Saville Road",
            "address_line_2": "The penthouse suite",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "country": 235,
            "postcode": "SN1 61665",
            "notes": "Is this a real address? Let's find out.",
        })

        self.assertTrue(form.is_valid())

        address = form.save()
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(address.user, self.primary_user)
        self.assertEqual(address.address_line_1, "1 Saville Road")
        self.assertEqual(address.address_line_2, "The penthouse suite")
        self.assertEqual(address.neighbourhood, "Mayfair")
        self.assertEqual(address.city, "London")
        self.assertEqual(address.state, "London")
        self.assertEqual(address.country_id, 235)
        self.assertEqual(address.postcode, "SN1 61665")
        self.assertEqual(address.notes, "Is this a real address? Let's find out.")


class TestContactFilterForm(BaseFormTestCase, TestCase):
    pass


class TestBaseContactFilterFormSet:
    pass


class TestContactForm(BaseFormTestCase, TestCase):
    def test_form_init_with_user(self) -> None:
        """
        Test that the ContactForm is correctly initialised setting the user_id to the form instance.
        """
        form = ContactForm(self.primary_user)       
        
        # Create Tags and Contacts for both Users, to ensure that only the primary Users'
        # Tags and Contacts appear in the respective querysets for selection.
        TagFactory.create_batch(3, user=self.other_user)
        TagFactory.create_batch(3, user=self.primary_user)
        ContactFactory.create_batch(2, user=self.other_user)
        ContactFactory.create_batch(2, user=self.primary_user)

        self.assertEqual(self.primary_user.id, form.instance.user_id)
        self.assertQuerySetEqual(Tag.objects.filter(user=self.primary_user), form.fields["tags"].queryset)
        self.assertQuerySetEqual(Contact.objects.filter(user=self.primary_user), form.fields["family_members"].queryset)

    def test_profession_field_empty_label(self) -> None:
        """
        Test that the profession field empty label is set as desired.
        """
        form = ContactForm(self.primary_user)
        self.assertEqual(form.fields["profession"].empty_label, "-- Select Profession --")

    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = ContactForm(self.primary_user)

        self.assertEqual(
            Counter([
                "anniversary", "dob", "dod", "family_members", "first_name", "gender",
                "is_business", "last_name", "middle_names", "nationalities", "nickname",
                "notes", "profession", "tags", "website", "year_met",
            ]),
            Counter(form.fields.keys())
        )

    def test_form_init_without_user(self) -> None:
        """
        Test that instantiation of the ContactForm fails without a valid user arg passed in.
        """
        with self.assertRaises(TypeError) as cm:
            form = ContactForm()

        self.assertEqual(str(cm.exception), "ContactForm.__init__() missing 1 required positional argument: 'user'")

    def test_overridden_field_types(self) -> None:
        """
        Test that fields where the type has been overridden from the default are the type desired.
        """
        form = ContactForm(self.primary_user)
        self.assertTrue(isinstance(form.fields["anniversary"], forms.DateField))
        self.assertTrue(isinstance(form.fields["dob"], forms.DateField))
        self.assertTrue(isinstance(form.fields["dod"], forms.DateField))

    def test_validates_with_only_required_fields(self) -> None:
        """
        Test that the form validates successfully with only the required fields.
        """
        form = ContactForm(self.primary_user, {
            "first_name": "Dave",
            "gender": constants.CONTACT_GENDER_MALE,
            "year_met": 2009,
        })
        
        self.assertTrue(form.is_valid())

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = ContactForm(self.primary_user, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["first_name", "gender", "year_met"]),
            Counter(list(form.errors.as_data()))
        )

    def test_validates_and_saves_with_comprehensive_data(self) -> None:
        """
        Test that the form validates successfully with comprehensive data including the required fields.
        """
        # Create a Tag and a Contact (potential FamilyMember) that ARE NOT
        # going to be associated with the saved Contact.
        TagFactory.create(user=self.primary_user)
        ContactFactory.create(user=self.primary_user)

        tag = TagFactory.create(user=self.primary_user)
        family_member = ContactFactory.create(user=self.primary_user)

        form = ContactForm(self.primary_user, {
            "anniversary_day": "1",
            "anniversary_month": "1",
            "anniversary_year": "2001",
            "dob_day": "22",
            "dob_month": "06",
            "dob_year": "1978",
            "dod_day": "31",
            "dod_month": "12",
            "dod_year": "2020",
            "family_members": [family_member.id],
            "first_name": "Max",
            "gender": constants.CONTACT_GENDER_MALE,
            "is_business": "on",
            "last_name": "Smith",
            "middle_names": "Egbert",
            "nationalities": [197],
            "nickname": "Maxbert",
            "notes": "Not a real person",
            "profession": 2,
            "tags": [tag.id],
            "website": "www.https.com",
            "year_met": "2001",
        })

        self.assertTrue(form.is_valid())

        contact = form.save()
        self.assertTrue(Contact.objects.filter(pk=contact.id).exists())
        self.assertEqual(contact.user, self.primary_user)
        self.assertEqual(contact.anniversary, datetime.date(2001, 1, 1))
        self.assertEqual(contact.dob, datetime.date(1978, 6, 22))
        self.assertEqual(contact.dod, datetime.date(2020, 12, 31))
        self.assertEqual(contact.first_name, "Max")
        self.assertEqual(contact.gender, constants.CONTACT_GENDER_MALE)
        self.assertEqual(contact.is_business, True)
        self.assertEqual(contact.last_name, "Smith")
        self.assertEqual(contact.middle_names, "Egbert")
        self.assertEqual(contact.nickname, "Maxbert")
        self.assertEqual(contact.notes, "Not a real person")
        self.assertEqual(contact.profession_id, 2)
        self.assertEqual(contact.website, "www.https.com")
        self.assertEqual(contact.year_met, 2001)
        self.assertEqual(1, contact.family_members.count())
        self.assertIn(family_member.id, contact.family_members.values_list("id", flat=True))
        self.assertEqual(1, contact.nationalities.count())
        self.assertIn(197, contact.nationalities.values_list("id", flat=True))
        self.assertEqual(1, contact.tags.count())
        self.assertIn(tag.id, contact.tags.values_list("id", flat=True))


class TestEmailForm(BaseFormTestCase, TestCase):
    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = EmailForm()

        self.assertEqual(
            Counter(["archived", "email", "email_types"]),
            Counter(form.fields.keys())
        )

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = EmailForm({"archived": True})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["email", "email_types"]),
            Counter(list(form.errors.as_data()))
        )

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that form validation is successful with valid data and an archived
        email is successfully saved to db.
        """
        pref_type_id = get_pref_contactable_type_id("EmailType")
        email_types: QuerySet = EmailType.objects.exclude(pk=pref_type_id).order_by("?")[:2]
        email_type_ids: List[int] = list(email_types.values_list("id", flat=True))

        form = EmailForm({
            "archived": True,
            "email": "superunique@email.com",
            "email_types": email_type_ids,
        })
        self.assertTrue(form.is_valid())

        email: Email = form.save(commit=False)
        email.contact = ContactFactory.create()
        email.save()
        form.save_m2m()

        self.assertTrue(Email.objects.filter(pk=email.id).exists())
        self.assertEqual(
            Counter(email_type_ids),
            Counter(email.email_types.values_list("id", flat=True))
        )
        self.assertEqual("superunique@email.com", email.email)

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that form validation is successful with valid data and an unarchived
        email is successfully saved to db.
        """
        email_types: QuerySet = EmailType.objects.order_by("?")[:2]
        email_type_ids: List[int] = list(email_types.values_list("id", flat=True))

        form = EmailForm({
            "archived": False,
            "email": "superunique@email.com",
            "email_types": email_type_ids,
        })
        self.assertTrue(form.is_valid())

        email: Email = form.save(commit=False)
        email.contact = ContactFactory.create()
        email.save()
        form.save_m2m()

        self.assertTrue(Email.objects.filter(pk=email.id).exists())
        self.assertEqual(
            Counter(email_type_ids),
            Counter(email.email_types.values_list("id", flat=True))
        )
        self.assertEqual("superunique@email.com", email.email)

    def test_not_validates_if_archived_and_pref(self) -> None:
        """
        Test that the form validation fails if the Email is set as archived, and
        linked with the 'preferred' EmailType, among other EmailTypes.
        """
        pref_type_id = get_pref_contactable_type_id("EmailType")
        non_pref_type = EmailType.objects.exclude(pk=pref_type_id).order_by("?").first()

        form = EmailForm({
            "archived": True,
            "email": fake.email(),
            "email_types": [pref_type_id, non_pref_type.id]
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["email_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(form.errors["email_types"], ["Being 'preferred' and archived is not allowed."])

    def test_not_validates_if_only_pref_type(self) -> None:
        """
        Test that the form validation fails if the Email is linked with the 'preferred'
        EmailType alone.
        """
        pref_type_id = get_pref_contactable_type_id("EmailType")

        form = EmailForm({
            "archived": False,
            "email": fake.email(),
            "email_types": [pref_type_id],
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["email_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(form.errors["email_types"], ["'Preferred' is not allowed as the only type."])

    def test_both_errors_thrown_if_only_pref_type_and_archived(self) -> None:
        """
        Test that the form validation fails if the Email is linked with the 'preferred'
        EmailType alone, AND it is archived. Ensure that both errors are thrown.
        """
        pref_type_id = get_pref_contactable_type_id("EmailType")

        form = EmailForm({
            "archived": True,
            "email": fake.email(),
            "email_types": [pref_type_id],
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["email_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(
            Counter([
                "'Preferred' is not allowed as the only type.",
                "Being 'preferred' and archived is not allowed."
            ]),
            Counter(form.errors["email_types"])
        )


class TestPhoneNumberForm(BaseFormTestCase, TestCase):
    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = PhoneNumberForm()

        self.assertEqual(
            Counter(["archived", "number", "phonenumber_types"]),
            Counter(form.fields.keys())
        )

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = PhoneNumberForm({"archived": True})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["number", "phonenumber_types"]),
            Counter(list(form.errors.as_data()))
        )

    def test_overridden_field_types(self) -> None:
        """
        Test that fields where the type has been overridden from the default are the type desired.
        """
        form = PhoneNumberForm()
        self.assertTrue(isinstance(form.fields["number"], CustomSplitPhoneNumberField))

    def test_phonenumber_prefix_field_empty_label(self) -> None:
        """
        Test that the phonenumber prefix field empty label (in this case, first and empty choice)
        is set as desired.
        """
        form = PhoneNumberForm()
        value, label = form.fields["number"].widget.widgets[0].choices[0]
        self.assertEqual(value, "")
        self.assertEqual(label, "-- Select Country Prefix --")

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that form validation is successful with valid data and an archived
        phone number is successfully saved to db.
        """
        pref_type_id = get_pref_contactable_type_id("PhoneNumberType")
        phonenumber_types: QuerySet = PhoneNumberType.objects.exclude(pk=pref_type_id).order_by("?")[:2]
        phonenumber_type_ids: List[int] = list(phonenumber_types.values_list("id", flat=True))

        form = PhoneNumberForm({
            "archived": True,
            "number_0": "GB",
            "number_1": "7123456789",
            "phonenumber_types": phonenumber_type_ids,
        })
        self.assertTrue(form.is_valid())

        phonenumber: PhoneNumber = form.save(commit=False)
        phonenumber.contact = ContactFactory.create()
        phonenumber.save()
        form.save_m2m()

        self.assertTrue(PhoneNumber.objects.filter(pk=phonenumber.id).exists())
        self.assertEqual(
            Counter(phonenumber_type_ids),
            Counter(phonenumber.phonenumber_types.values_list("id", flat=True))
        )
        self.assertEqual("+447123456789", phonenumber.number)

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that form validation is successful with valid data and an unarchived
        phonenumber is successfully saved to db.
        """
        phonenumber_types: QuerySet = PhoneNumberType.objects.order_by("?")[:2]
        phonenumber_type_ids: List[int] = list(phonenumber_types.values_list("id", flat=True))

        form = PhoneNumberForm({
            "archived": False,
            "number_0": "US",
            "number_1": "2015550123",
            "phonenumber_types": phonenumber_type_ids,
        })
        self.assertTrue(form.is_valid())

        phonenumber: PhoneNumber = form.save(commit=False)
        phonenumber.contact = ContactFactory.create()
        phonenumber.save()
        form.save_m2m()

        self.assertTrue(PhoneNumber.objects.filter(pk=phonenumber.id).exists())
        self.assertEqual(
            Counter(phonenumber_type_ids),
            Counter(phonenumber.phonenumber_types.values_list("id", flat=True))
        )
        self.assertEqual("+12015550123", phonenumber.number)

    def test_not_validates_if_archived_and_pref(self) -> None:
        """
        Test that the form validation fails if the PhoneNumber is set as archived, and
        linked with the 'preferred' PhoneNumberType, among other PhoneNumberTypes.
        """
        pref_type_id = get_pref_contactable_type_id("PhoneNumberType")
        non_pref_type = PhoneNumberType.objects.exclude(pk=pref_type_id).order_by("?").first()

        form = PhoneNumberForm({
            "archived": True,
            "number_0": "US",
            "number_1": "2015550123",
            "phonenumber_types": [pref_type_id, non_pref_type.id]
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["phonenumber_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(form.errors["phonenumber_types"], ["Being 'preferred' and archived is not allowed."])

    def test_not_validates_if_only_pref_type(self) -> None:
        """
        Test that the form validation fails if the PhoneNumber is linked with the 'preferred'
        PhoneNumberType alone.
        """
        pref_type_id = get_pref_contactable_type_id("PhoneNumberType")

        form = PhoneNumberForm({
            "archived": False,
            "number_0": "GB",
            "number_1": "7123456789",
            "phonenumber_types": [pref_type_id],
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["phonenumber_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(form.errors["phonenumber_types"], ["'Preferred' is not allowed as the only type."])

    def test_both_errors_thrown_if_only_pref_type_and_archived(self) -> None:
        """
        Test that the form validation fails if the Email is linked with the 'preferred'
        PhoneNumberType alone, AND it is archived. Ensure that both errors are thrown.
        """
        pref_type_id = get_pref_contactable_type_id("PhoneNumberType")

        form = PhoneNumberForm({
            "archived": True,
            "number_0": "GB",
            "number_1": "7987654321",
            "phonenumber_types": [pref_type_id],
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["phonenumber_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(
            Counter([
                "'Preferred' is not allowed as the only type.",
                "Being 'preferred' and archived is not allowed."
            ]),
            Counter(form.errors["phonenumber_types"])
        )


class TestTagForm(BaseFormTestCase, TestCase):
    def test_form_init_with_user(self) -> None:
        """
        Test that the TagForm is correctly initialised setting the user_id to the form instance.
        """
        form = TagForm(self.primary_user)       
        
        # Create Contacts for both Users, to ensure that only the primary Users'
        # Contacts appear in the queryset for selection.
        ContactFactory.create_batch(2, user=self.other_user)
        ContactFactory.create_batch(2, user=self.primary_user)

        self.assertEqual(self.primary_user.id, form.instance.user_id)
        self.assertQuerySetEqual(Contact.objects.filter(user=self.primary_user), form.fields["contacts"].queryset)
        
    def test_form_init_without_user(self) -> None:
        """
        Test that TagForm instantiation fails when no user is provided to the form instance.
        """
        with self.assertRaises(TypeError) as cm:
            form = TagForm()
            
        self.assertEqual(str(cm.exception), "TagForm.__init__() missing 1 required positional argument: 'user'")

    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = TagForm(self.primary_user)

        self.assertEqual(
            Counter(["contacts", "name"]),
            Counter(form.fields.keys())
        )

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = TagForm(self.primary_user, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["contacts", "name"]),
            Counter(list(form.errors.as_data()))
        )

    def test_overridden_field_types(self) -> None:
        """
        Test that fields where the type has been overridden from the default are the type desired.
        """
        form = TagForm(self.primary_user)
        self.assertTrue(isinstance(form.fields["contacts"], forms.ModelMultipleChoiceField))

    def test_validates_and_saves_with_comprehensive_valid_data(self) -> None:
        """
        Test that form validation is successful with valid data and a tag and its contact
        associations are successfully saved to db.
        """
        contacts = ContactFactory.create_batch(12, user=self.primary_user)
        related_contact_ids = [contact.id for contact in contacts[:4]]

        form = TagForm(self.primary_user, {
            "contacts": related_contact_ids,
            "name": "TesterTag",
        })
        self.assertTrue(form.is_valid())

        tag: Tag = form.save()

        self.assertTrue(Tag.objects.filter(pk=tag.id).exists())
        self.assertEqual(
            Counter(related_contact_ids),
            Counter(tag.contact_set.values_list("id", flat=True))
        )
        self.assertEqual("TesterTag", tag.name)


class TestTenancyForm(BaseFormTestCase, TestCase):
    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = TenancyForm(user=self.primary_user)

        self.assertEqual(
            Counter(["address", "archived", "tenancy_types"]),
            Counter(form.fields.keys())
        )

    def test_form_init_with_user(self) -> None:
        """
        Test that the TenancyForm is correctly initialised setting the user_id to the form instance.
        """
        form = TenancyForm(user=self.primary_user)

        # Create Addresses for both Users, to ensure that only the primary Users'
        # Addresses appear in the queryset for selection.
        AddressFactory.create_batch(3, user=self.other_user)
        AddressFactory.create_batch(3, user=self.primary_user)

        self.assertQuerySetEqual(Address.objects.filter(user=self.primary_user), form.fields["address"].queryset)

    def test_form_init_without_user(self) -> None:
        """
        Test that TenancyForm instantiation fails when no user is provided to the form instance.
        """
        with self.assertRaises(TypeError) as cm:
            form = TenancyForm()
            
        self.assertEqual(str(cm.exception), "TenancyForm.__init__() missing 1 required keyword argument: 'user'")

    def test_address_field_empty_label(self) -> None:
        """
        Test that the address empty_label is set as desired.
        """
        form = TenancyForm(user=self.primary_user)

        self.assertEqual("-- Select Address --", form.fields["address"].empty_label)

    def test_validates_with_only_required_fields(self) -> None:
        """
        Test that the form validates successfully with only the required fields.
        """
        address = AddressFactory.create(user=self.primary_user)
        form = TenancyForm({
            "address": address,
            "tenancy_types": AddressType.objects.order_by("?")[:2]
        }, user=self.primary_user)
        
        self.assertTrue(form.is_valid())

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = TenancyForm({"archived": True}, user=self.primary_user)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["address", "tenancy_types"]),
            Counter(list(form.errors.as_data()))
        )

    def test_overridden_field_types(self) -> None:
        """
        Test that fields where the type has been overridden from the default are the type desired.
        """
        form = TenancyForm(user=self.primary_user)
        self.assertTrue(isinstance(form.fields["address"], forms.ModelChoiceField))

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that form validation is successful with valid data and an archived
        tenancy is successfully saved to db.
        """
        pref_type_id = get_pref_contactable_type_id("AddressType")
        address_types: QuerySet = AddressType.objects.exclude(pk=pref_type_id).order_by("?")[:2]
        address_type_ids: List[int] = list(address_types.values_list("id", flat=True))
        address = AddressFactory.create(user=self.primary_user)

        form = TenancyForm({
            "address": address.id,
            "archived": True,
            "tenancy_types": address_type_ids,
        }, user=self.primary_user)
        self.assertTrue(form.is_valid())

        tenancy: Tenancy = form.save(commit=False)
        contact: Contact = ContactFactory.create(user=self.primary_user)
        tenancy.contact = contact
        tenancy.save()
        form.save_m2m()

        self.assertTrue(Tenancy.objects.filter(pk=tenancy.id).exists())
        self.assertEqual(
            Counter(address_type_ids),
            Counter(tenancy.tenancy_types.values_list("id", flat=True))
        )
        self.assertEqual(address.id, tenancy.address_id)
        self.assertEqual(contact.id, tenancy.contact_id)
        self.assertTrue(tenancy.archived)

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that form validation is successful with valid data and an unarchived
        Tenancy is successfully saved to db.
        """
        address_types: QuerySet = AddressType.objects.order_by("?")[:2]
        address_type_ids: List[int] = list(address_types.values_list("id", flat=True))
        address = AddressFactory.create(user=self.primary_user)

        form = TenancyForm({
            "address": address.id,
            "archived": False,
            "tenancy_types": address_type_ids,
        }, user=self.primary_user)
        self.assertTrue(form.is_valid())

        tenancy: Tenancy = form.save(commit=False)
        contact: Contact = ContactFactory.create(user=self.primary_user)
        tenancy.contact = contact
        tenancy.save()
        form.save_m2m()

        self.assertTrue(Tenancy.objects.filter(pk=tenancy.id).exists())
        self.assertEqual(
            Counter(address_type_ids),
            Counter(tenancy.tenancy_types.values_list("id", flat=True))
        )
        self.assertEqual(address.id, tenancy.address_id)
        self.assertEqual(contact.id, tenancy.contact_id)
        self.assertFalse(tenancy.archived)

    def test_not_validates_if_archived_and_pref(self) -> None:
        """
        Test that the form validation fails if the Tenancy is set as archived, and
        linked with the 'preferred' AddressType, among other AddressTypes.
        """
        pref_type_id = get_pref_contactable_type_id("AddressType")
        non_pref_type = AddressType.objects.exclude(pk=pref_type_id).order_by("?").first()
        address = AddressFactory.create(user=self.primary_user)

        form = TenancyForm({
            "address": address.id,
            "archived": True,
            "tenancy_types": [pref_type_id, non_pref_type.id]
        }, user=self.primary_user)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["tenancy_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(form.errors["tenancy_types"], ["Being 'preferred' and archived is not allowed."])

    def test_not_validates_if_only_pref_type(self) -> None:
        """
        Test that the form validation fails if the Tenancy is linked with the 'preferred'
        AddressType alone.
        """
        pref_type_id = get_pref_contactable_type_id("AddressType")
        address = AddressFactory.create(user=self.primary_user)

        form = TenancyForm({
            "address": address.id,
            "archived": False,
            "tenancy_types": [pref_type_id],
        }, user=self.primary_user)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["tenancy_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(form.errors["tenancy_types"], ["'Preferred' is not allowed as the only type."])

    def test_both_errors_thrown_if_only_pref_type_and_archived(self) -> None:
        """
        Test that the form validation fails if the Email is linked with the 'preferred'
        AddressType alone, AND it is archived. Ensure that both errors are thrown.
        """
        pref_type_id = get_pref_contactable_type_id("AddressType")
        address = AddressFactory.create(user=self.primary_user)

        form = TenancyForm({
            "address": address.id,
            "archived": True,
            "tenancy_types": [pref_type_id],
        }, user=self.primary_user)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["tenancy_types"]),
            Counter(list(form.errors.as_data()))
        )
        self.assertEqual(
            Counter([
                "'Preferred' is not allowed as the only type.",
                "Being 'preferred' and archived is not allowed."
            ]),
            Counter(form.errors["tenancy_types"])
        )


class TestWalletAddressForm(BaseFormTestCase, TestCase):
    def test_fields_present(self) -> None:
        """
        Test that the correct fields are included/excluded.
        """
        form = WalletAddressForm()

        self.assertEqual(
            Counter(["address", "archived", "network", "transmission"]),
            Counter(form.fields.keys())
        )

    def test_network_and_transmission_fields_empty_labels(self) -> None:
        """
        Test that the network empty_label is set as desired, and that the first choice for
        transmission (empty label) is set as desired.
        """
        form = WalletAddressForm()

        self.assertEqual("-- Select Network --", form.fields["network"].empty_label)
        value, label = form.fields["transmission"].choices[0]
        self.assertIsNone(value)
        self.assertEqual("-- Select Transmission --", label)

    def test_validates_with_only_required_fields(self) -> None:
        """
        Test that the form validates successfully with only the required fields.
        """
        network = CryptoNetwork.objects.order_by("?").first()
        form = WalletAddressForm({
            "address": "0xjdfhgkjh2kjh2345jkh23k4jh234jkh23jk4h",
            "network": network.id,
            "transmission": random.choice([
                constants.WALLETADDRESS_TRANSMISSION_THEY_RECEIVE,
                constants.WALLETADDRESS_TRANSMISSION_YOU_RECEIVE,
            ]),
        })
        
        self.assertTrue(form.is_valid())

    def test_not_validates_without_required_fields(self) -> None:
        """
        Test that the form fails to validate successfully without the required fields.
        """
        form = WalletAddressForm({"archived": True})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            Counter(["address", "network", "transmission"]),
            Counter(list(form.errors.as_data()))
        )

    def test_validates_and_saves_with_comprehensive_valid_data(self) -> None:
        """
        Test that form validation is successful with valid data and a wallet address
        is successfully saved to db.
        """
        network = CryptoNetwork.objects.order_by("?").first()

        form = WalletAddressForm({
            "address": "0x8sd7fg89sd7fg89s7as89d7fs98d7f8s9d7fsd9f",
            "archived": fake.boolean(),
            "network": network.id,
            "transmission": random.choice([
                constants.WALLETADDRESS_TRANSMISSION_THEY_RECEIVE,
                constants.WALLETADDRESS_TRANSMISSION_YOU_RECEIVE,
            ]),
        })
        self.assertTrue(form.is_valid())

        wallet_address: WalletAddress = form.save(commit=False)
        contact: Contact = ContactFactory.create(user=self.primary_user)
        wallet_address.contact = contact
        wallet_address.save()

        self.assertTrue(WalletAddress.objects.filter(pk=wallet_address.id).exists())
        self.assertIn(wallet_address.transmission, [
            constants.WALLETADDRESS_TRANSMISSION_THEY_RECEIVE,
            constants.WALLETADDRESS_TRANSMISSION_YOU_RECEIVE,
        ])
        self.assertEqual(wallet_address.contact_id, contact.id)
        self.assertEqual(wallet_address.network_id, network.id)
        self.assertEqual(wallet_address.address, "0x8sd7fg89sd7fg89s7as89d7fs98d7f8s9d7fsd9f")


class TestEmailCreateFormSet(BaseFormTestCase, TestCase):
    def test_delete_not_present(self) -> None:
        """
        Test that the delete fields are not present as this is the creation form.
        """
        formset = EmailCreateFormSet()
        for form in formset.forms:
            self.assertNotIn("DELETE", form.fields)

    def test_not_validates_with_multiple_preferred_emails(self) -> None:
        """
        Test that form validation fails if more than one email in the formset is set as EmailType, 'preferred'.
        """
        pref_type_id = str(get_pref_contactable_type_id("EmailType"))
        non_pref_type = EmailType.objects.exclude(id=pref_type_id).order_by("?").first()
        non_pref_type_id = str(non_pref_type.id)

        data = {
            "email_set-TOTAL_FORMS": "2",
            "email_set-INITIAL_FORMS": "0",
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",

            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [pref_type_id, non_pref_type_id],
            "email_set-0-id": "",
            
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [pref_type_id, non_pref_type_id],
            "email_set-1-id": "",
        }

        formset = EmailCreateFormSet(data=data)
        self.assertFalse(formset.is_valid())
        self.assertIn("Only one may be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_without_preferred_email_when_unarchived(self) -> None:
        """
        Test that form validation fails if no email in the formset is set as EmailType, 'preferred'.
        """
        pref_type_id = str(get_pref_contactable_type_id("EmailType"))
        non_pref_type = EmailType.objects.exclude(id=pref_type_id).order_by("?").first()
        non_pref_type_id = str(non_pref_type.id)

        data = {
            "email_set-TOTAL_FORMS": "2",
            "email_set-INITIAL_FORMS": "0",
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",

            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [non_pref_type_id],
            "email_set-0-id": "",
            
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [non_pref_type_id],
            "email_set-1-id": "",
        }

        formset = EmailCreateFormSet(data=data)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that formset validation is successful with valid data and emails are successfully saved to db
        when emails are unarchived.
        """
        pref_type_id = get_pref_contactable_type_id("EmailType")
        non_pref_type = EmailType.objects.exclude(id=pref_type_id).order_by("?").first()
        non_pref_type_id = non_pref_type.id

        data = {
            "email_set-TOTAL_FORMS": "2",
            "email_set-INITIAL_FORMS": "0",
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",

            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [str(pref_type_id), str(non_pref_type_id)],
            "email_set-0-id": "",
            
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [str(non_pref_type_id)],
            "email_set-1-id": "",
        }

        formset = EmailCreateFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = ContactFactory.create()
        formset.save()

        self.assertEqual(Email.objects.all().count(), 2)
        
        pref_email_query = Email.objects.filter(email="one@email.com")
        self.assertTrue(pref_email_query.exists())

        pref_email = pref_email_query.first()
        self.assertFalse(pref_email.archived)
        self.assertEqual(
            Counter([pref_type_id, non_pref_type_id]),
            Counter(pref_email.email_types.values_list("id", flat=True))
        )
        
        secondary_email_query = Email.objects.filter(email="two@email.com")
        self.assertTrue(secondary_email_query.exists())

        secondary_email = secondary_email_query.first()
        self.assertFalse(secondary_email.archived)
        self.assertEqual(
            Counter([non_pref_type_id]),
            Counter(secondary_email.email_types.values_list("id", flat=True))
        )

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that formset validation is successful with valid data and emails are successfully saved to db
        when all emails are archived - ensure that despite not having any 'preferred' email, validation and
        save is still successful.
        """
        pref_type_id = get_pref_contactable_type_id("EmailType")
        non_pref_type = EmailType.objects.exclude(id=pref_type_id).order_by("?").first()
        non_pref_type_id = non_pref_type.id

        data = {
            "email_set-TOTAL_FORMS": "2",
            "email_set-INITIAL_FORMS": "0",
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",

            "email_set-0-archived": True,
            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [str(non_pref_type_id)],
            "email_set-0-id": "",
            
            "email_set-1-archived": True,
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [str(non_pref_type_id)],
            "email_set-1-id": "",
        }

        formset = EmailCreateFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = ContactFactory.create()
        formset.save()

        self.assertEqual(Email.objects.all().count(), 2)
        
        first_email_query = Email.objects.filter(email="one@email.com")
        self.assertTrue(first_email_query.exists())

        first_email = first_email_query.first()
        self.assertTrue(first_email.archived)
        self.assertEqual(
            Counter([non_pref_type_id]),
            Counter(first_email.email_types.values_list("id", flat=True))
        )
        
        second_email_query = Email.objects.filter(email="two@email.com")
        self.assertTrue(second_email_query.exists())

        second_email = second_email_query.first()
        self.assertTrue(second_email.archived)
        self.assertEqual(
            Counter([non_pref_type_id]),
            Counter(second_email.email_types.values_list("id", flat=True))
        )


class TestEmailUpdateFormSet(BaseFormTestCase, TestCase):
    def _get_email_type_ids_for_email(self, email: Email) -> None:
        return list(map(
            lambda id: str(id), email.email_types.all().values_list("id", flat=True)
        ))

    def test_delete_present(self) -> None:
        """
        Test that the delete fields are present as this is the update form.
        """
        contact = ContactFactory.create()
        formset = EmailUpdateFormSet(instance=contact)
        for form in formset.forms:
            self.assertIn("DELETE", form.fields)

    def test_delete_successful(self) -> None:
        """
        Test that when delete is selected, the Email is successfully deleted from db.
        """
        contact = ContactFactory.create()
        pref_email = EmailFactory.create(contact=contact)
        non_pref_email = EmailFactory.create(contact=contact)

        data = {
            "email_set-TOTAL_FORMS": "2",
            "email_set-INITIAL_FORMS": "2",
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",

            "email_set-0-archived": False,
            "email_set-0-contact": str(contact.id),
            "email_set-0-email": pref_email.email,
            "email_set-0-email_types": self._get_email_type_ids_for_email(pref_email),
            "email_set-0-id": str(pref_email.id),
            
            "email_set-1-archived": False,
            "email_set-1-contact": str(contact.id),
            "email_set-1-DELETE": True,
            "email_set-1-email": non_pref_email.email,
            "email_set-1-email_types": self._get_email_type_ids_for_email(non_pref_email),
            "email_set-1-id": str(non_pref_email.id),
        }

        formset = EmailUpdateFormSet(data=data, instance=contact)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(1, Email.objects.count())
        self.assertFalse(Email.objects.filter(email=non_pref_email.email).exists())

    def test_delete_preferred_unsuccessful_if_no_replacement(self) -> None:
        """
        Test that when delete is selected on the 'preferred' Email, form validation fails unless
        there is a newly selected 'preferred' Email.
        """
        contact = ContactFactory.create()
        pref_email = EmailFactory.create(contact=contact)
        non_pref_email = EmailFactory.create(contact=contact)

        data = {
            "email_set-TOTAL_FORMS": "2",
            "email_set-INITIAL_FORMS": "2",
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",

            "email_set-0-archived": False,
            "email_set-0-contact": str(contact.id),
            "email_set-0-DELETE": True,
            "email_set-0-email": pref_email.email,
            "email_set-0-email_types": self._get_email_type_ids_for_email(pref_email),
            "email_set-0-id": str(pref_email.id),
            
            "email_set-1-archived": False,
            "email_set-1-contact": str(contact.id),
            "email_set-1-email": non_pref_email.email,
            "email_set-1-email_types": self._get_email_type_ids_for_email(non_pref_email),
            "email_set-1-id": str(non_pref_email.id),
        }

        formset = EmailUpdateFormSet(data=data, instance=contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())