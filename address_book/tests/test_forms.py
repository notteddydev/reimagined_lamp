import datetime

from collections import Counter

from django import forms
from django.test import TestCase

from address_book import constants
from address_book.factories.contact_factories import ContactFactory
from address_book.factories.tag_factories import TagFactory
from address_book.factories.user_factories import UserFactory
from address_book.forms import AddressForm, ContactForm
from address_book.models import Address, Contact, Tag


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
            
        self.assertEquals(str(cm.exception), "AddressForm.__init__() missing 1 required positional argument: 'user'")

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
        pass