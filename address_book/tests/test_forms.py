import datetime
import random

from collections import Counter
from django import forms
from django.apps import apps
from django.db.models import QuerySet
from django.forms.models import model_to_dict
from django.test import TestCase
from faker import Faker
from typing import List, Optional

from address_book import constants
from address_book.factories.address_factories import AddressFactory
from address_book.factories.contact_factories import ContactFactory
from address_book.factories.email_factories import EmailFactory
from address_book.factories.phonenumber_factories import AddressPhoneNumberFactory, ContactPhoneNumberFactory
from address_book.factories.tag_factories import TagFactory
from address_book.factories.user_factories import UserFactory
from address_book.forms import AddressForm, AddressPhoneNumberFormSet, ContactForm, ContactPhoneNumberFormSet, CustomSplitPhoneNumberField, EmailForm, EmailFormSet, PhoneNumberForm, TagForm, TenancyForm, TenancyFormSet, WalletAddressForm
from address_book.models import Address, AddressType, Contact, Contactable, CryptoNetwork, Email, EmailType, PhoneNumber, PhoneNumberType, Tag, Tenancy, WalletAddress

fake = Faker()


def get_contactable_type_ids_for_contactable(contactable: Contactable) -> None:
    """
    Get a list of the 'contactable_types' (i.e. email_types / phonenumber_types) ids for a given
    'contactable' (i.e. email / phonenumber) and return them as strings. This is handy for providing
    data for forms.
    """
    return list(map(
        lambda id: str(id), contactable.contactable_types.all().values_list("id", flat=True)
    ))


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
    def _test_data_produces_expected_error_for_expected_field(self, contact_data: dict, errorfield_to_test: str, errormsg_to_check: str) -> None:
        """
        Common logic for checking that provided 'contact_data' raises a given error for a given field.
        """
        contact = ContactFactory.build(**contact_data)
        form = ContactForm(self.primary_user, model_to_dict(contact))
        self.assertFalse(form.is_valid())
        self.assertIn(errorfield_to_test, form.errors)
        self.assertIn(errormsg_to_check, form.errors[errorfield_to_test])

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

    def test_dod_lt_dob_fails_validation(self) -> None:
        """
        Test that a DoD < DoB fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1), # Add anniversary so that factory doesn't break due to deliberately incorrect dob / dod combo
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2000, 12, 31),
            "year_met": 2001 # Add year_met so that factory doesn't break due to deliberately incorrect dob / dod combo
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="dob",
            errormsg_to_check="Date of birth may not be after date of passing."
        )

    def test_dod_lt_anniversary_fails_validation(self) -> None:
        """
        Test that a DoD < anniversary fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2011, 1, 1),
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2010, 1, 1),
            "year_met": 2001 # Add year_met so that factory doesn't break due to deliberately incorrect dob / dod combo
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="anniversary",
            errormsg_to_check="Anniversary must be sooner than the date of passing."
        )

    def test_dod_lt_yearmet_fails_validation(self) -> None:
        """
        Test that a DoD < year_met fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1), # Add anniversary so that factory doesn't break due to deliberately incorrect dob / dod combo
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2000, 12, 31),
            "year_met": 2002
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="year_met",
            errormsg_to_check="Year met may not be after date of passing."
        )

    def test_yearmet_lt_dob_fails_validation(self) -> None:
        """
        Test that a year_met < DoB fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1), # Add anniversary so that factory doesn't break due to deliberately incorrect dob / dod combo
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2000, 12, 31),
            "year_met": 1999
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="year_met",
            errormsg_to_check="Year met may not be before the date of birth."
        )

    def test_anniversary_lte_dob_fails_validation(self) -> None:
        """
        Test that an anniversary <= DoB fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2000, 1, 1),
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2000, 12, 31),
            "year_met": 2001 # Add year_met so that factory doesn't break due to deliberately incorrect dob / dod combo
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="anniversary",
            errormsg_to_check="Anniversary must be greater than the date of birth."
        )
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1),
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2000, 12, 31),
            "year_met": 2001 # Add year_met so that factory doesn't break due to deliberately incorrect dob / dod combo
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="anniversary",
            errormsg_to_check="Anniversary must be greater than the date of birth."
        )

    def test_dod_is_future_fails_validation(self) -> None:
        """
        Test that a DoD set to a future date fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1), # Add anniversary so that factory doesn't break due to deliberately incorrect dob / dod combo
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(datetime.datetime.now().year + 1, 12, 31),
            "year_met": 2001 # Add year_met so that factory doesn't break due to deliberately incorrect dob / dod combo
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="dod",
            errormsg_to_check="Date of passing may not be set to a future date."
        )

    def test_dob_is_future_fails_validation(self) -> None:
        """
        Test that a DoB set to a future date fails validation.
        """
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1), # Add anniversary so that factory doesn't break due to deliberately incorrect dob / dod combo
            "dob": datetime.date(datetime.datetime.now().year + 1, 12, 31),
            "dod": datetime.date(2000, 12, 31),
            "year_met": 2001 # Add year_met so that factory doesn't break due to deliberately incorrect dob / dod combo
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="dob",
            errormsg_to_check="Date of birth may not be set to a future date."
        )

    def test_year_met_is_future_fails_validation(self) -> None:
        """
        Test that a year_met set to a future year fails validation.
        """
        bad_year = datetime.datetime.now().year + 2
        contact_data = {
            "anniversary": datetime.date(2001, 1, 1), # Add anniversary so that factory doesn't break due to deliberately incorrect dob / dod combo
            "dob": datetime.date(2001, 1, 1),
            "dod": datetime.date(2000, 12, 31),
            "year_met": bad_year
        }
        self._test_data_produces_expected_error_for_expected_field(
            contact_data=contact_data,
            errorfield_to_test="year_met",
            errormsg_to_check=f"Select a valid choice. {bad_year} is not one of the available choices."
        )


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


class TestEmailFormSet(BaseFormTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.contact = ContactFactory.create(user=self.primary_user)
        self.pref_type = EmailType.objects.preferred().first()
        self.non_pref_types = EmailType.objects.exclude(pk=self.pref_type.id).order_by("?")
        self.non_pref_type = self.non_pref_types.first()

    def _create_email(self, pref: bool, contact: Optional[Contact] = None):
        """
        Create an Email for a provided Contact (or not); optionally make it the preferred email.
        """
        if pref:
            email_types = [self.pref_type, self.non_pref_type]
        else:
            email_types = self.non_pref_types[:2]
        return EmailFactory.create(contact=contact or self.contact, email_types=email_types)
    
    def _get_management_form_data(self, initial: Optional[int] = 0, total: int = 2):
        """
        Create management form data for an Email FormSet.
        """
        return {
            "email_set-TOTAL_FORMS": str(total),
            "email_set-INITIAL_FORMS": str(initial),
            "email_set-MIN_NUM_FORMS": "0",
            "email_set-MAX_NUM_FORMS": "1000",
        }

    def test_delete_present(self) -> None:
        """
        Test that the delete fields are present.
        """
        formset = EmailFormSet(instance=self.contact)
        for form in formset.forms:
            self.assertIn("DELETE", form.fields)

    def test_delete_successful(self) -> None:
        """
        Test that when delete is selected, the Email is successfully deleted from db.
        """
        pref_email = self._create_email(pref=True)
        non_pref_email = self._create_email(pref=False)

        data = {
            **self._get_management_form_data(initial=2),

            "email_set-0-archived": False,
            "email_set-0-contact": str(self.contact.id),
            "email_set-0-email": pref_email.email,
            "email_set-0-email_types": get_contactable_type_ids_for_contactable(pref_email),
            "email_set-0-id": str(pref_email.id),
            
            "email_set-1-archived": False,
            "email_set-1-contact": str(self.contact.id),
            "email_set-1-DELETE": True,
            "email_set-1-email": non_pref_email.email,
            "email_set-1-email_types": get_contactable_type_ids_for_contactable(non_pref_email),
            "email_set-1-id": str(non_pref_email.id),
        }

        formset = EmailFormSet(data=data, instance=self.contact)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(1, Email.objects.count())
        self.assertFalse(Email.objects.filter(email=non_pref_email.email).exists())

    def test_delete_preferred_unsuccessful_if_no_replacement(self) -> None:
        """
        Test that when delete is selected on the 'preferred' Email, form validation fails unless
        there is a newly selected 'preferred' Email.
        """
        pref_email = self._create_email(pref=True)
        non_pref_email = self._create_email(pref=False)

        data = {
            **self._get_management_form_data(initial=2),

            "email_set-0-archived": False,
            "email_set-0-contact": str(self.contact.id),
            "email_set-0-DELETE": True,
            "email_set-0-email": pref_email.email,
            "email_set-0-email_types": get_contactable_type_ids_for_contactable(pref_email),
            "email_set-0-id": str(pref_email.id),
            
            "email_set-1-archived": False,
            "email_set-1-contact": str(self.contact.id),
            "email_set-1-email": non_pref_email.email,
            "email_set-1-email_types": get_contactable_type_ids_for_contactable(non_pref_email),
            "email_set-1-id": str(non_pref_email.id),
        }

        formset = EmailFormSet(data=data, instance=self.contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_with_multiple_preferred_emails(self) -> None:
        """
        Test that form validation fails if more than one email in the formset is set as EmailType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [self.pref_type.id, self.non_pref_type.id],
            "email_set-0-id": "",
            
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [self.pref_type.id, self.non_pref_type.id],
            "email_set-1-id": "",
        }

        formset = EmailFormSet(data=data, instance=self.contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("Only one may be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_without_preferred_email_when_unarchived(self) -> None:
        """
        Test that form validation fails if no email in the formset is set as EmailType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [self.non_pref_type.id],
            "email_set-0-id": "",
            
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [self.non_pref_type.id],
            "email_set-1-id": "",
        }

        formset = EmailFormSet(data=data, instance=self.contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that formset validation is successful with valid data and emails are successfully saved to db
        when emails are unarchived.
        """
        data = {
            **self._get_management_form_data(),

            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [self.pref_type.id, self.non_pref_type.id],
            "email_set-0-id": "",
            
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [self.non_pref_type.id],
            "email_set-1-id": "",
        }

        formset = EmailFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = ContactFactory.create()
        formset.save()

        self.assertEqual(Email.objects.all().count(), 2)
        
        pref_email_query = Email.objects.filter(email="one@email.com")
        self.assertTrue(pref_email_query.exists())

        pref_email = pref_email_query.first()
        self.assertFalse(pref_email.archived)
        self.assertEqual(
            Counter([self.pref_type.id, self.non_pref_type.id]),
            Counter(pref_email.email_types.values_list("id", flat=True))
        )
        
        secondary_email_query = Email.objects.filter(email="two@email.com")
        self.assertTrue(secondary_email_query.exists())

        secondary_email = secondary_email_query.first()
        self.assertFalse(secondary_email.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(secondary_email.email_types.values_list("id", flat=True))
        )

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that formset validation is successful with valid data and emails are successfully saved to db
        when all emails are archived - ensure that despite not having any 'preferred' email, validation and
        save is still successful.
        """
        data = {
            **self._get_management_form_data(),

            "email_set-0-archived": True,
            "email_set-0-contact": "",
            "email_set-0-email": "one@email.com",
            "email_set-0-email_types": [self.non_pref_type.id],
            "email_set-0-id": "",
            
            "email_set-1-archived": True,
            "email_set-1-contact": "",
            "email_set-1-email": "two@email.com",
            "email_set-1-email_types": [self.non_pref_type.id],
            "email_set-1-id": "",
        }

        formset = EmailFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = ContactFactory.create()
        formset.save()

        self.assertEqual(Email.objects.all().count(), 2)
        
        first_email_query = Email.objects.filter(email="one@email.com")
        self.assertTrue(first_email_query.exists())

        first_email = first_email_query.first()
        self.assertTrue(first_email.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(first_email.email_types.values_list("id", flat=True))
        )
        
        second_email_query = Email.objects.filter(email="two@email.com")
        self.assertTrue(second_email_query.exists())

        second_email = second_email_query.first()
        self.assertTrue(second_email.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(second_email.email_types.values_list("id", flat=True))
        )

    
class TestContactPhoneNumberFormSet(BaseFormTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.contact = ContactFactory.create(user=self.primary_user)
        self.pref_type = PhoneNumberType.objects.preferred().first()
        self.non_pref_types = PhoneNumberType.objects.exclude(pk=self.pref_type.id).order_by("?")
        self.non_pref_type = self.non_pref_types.first()

    def _create_phonenumber(self, pref: bool, contact: Optional[Contact] = None):
        """
        Create a PhoneNumber for a provided Contact (or not); optionally make it the preferred PhoneNumber.
        """
        if pref:
            phonenumber_types = [self.pref_type, self.non_pref_type]
        else:
            phonenumber_types = self.non_pref_types[:2]
        return ContactPhoneNumberFactory.create(
            contact=contact or self.contact,
            phonenumber_types=phonenumber_types
        )
    
    def _get_management_form_data(self, initial: Optional[int] = 0, total: int = 2):
        """
        Create management form data for a PhoneNumber FormSet.
        """
        return {
            "phonenumber_set-TOTAL_FORMS": str(total),
            "phonenumber_set-INITIAL_FORMS": str(initial),
            "phonenumber_set-MIN_NUM_FORMS": "0",
            "phonenumber_set-MAX_NUM_FORMS": "1000",
        }

    def test_delete_present(self) -> None:
        """
        Test that the delete fields are present.
        """
        formset = ContactPhoneNumberFormSet(instance=self.contact)
        for form in formset.forms:
            self.assertIn("DELETE", form.fields)

    def test_delete_successful(self) -> None:
        """
        Test that when delete is selected, the PhoneNumber is successfully deleted from db.
        """
        pref_phonenumber = self._create_phonenumber(pref=True)
        non_pref_phonenumber = self._create_phonenumber(pref=False)

        data = {
            **self._get_management_form_data(initial=2),

            "phonenumber_set-0-archived": False,
            "phonenumber_set-0-contact": str(self.contact.id),
            "phonenumber_set-0-number_0": pref_phonenumber.country_code,
            "phonenumber_set-0-number_1": pref_phonenumber.national_number,
            "phonenumber_set-0-phonenumber_types": get_contactable_type_ids_for_contactable(pref_phonenumber),
            "phonenumber_set-0-id": str(pref_phonenumber.id),
            
            "phonenumber_set-1-archived": False,
            "phonenumber_set-1-contact": str(self.contact.id),
            "phonenumber_set-1-DELETE": True,
            "phonenumber_set-1-number_0": non_pref_phonenumber.country_code,
            "phonenumber_set-1-number_1": non_pref_phonenumber.national_number,
            "phonenumber_set-1-phonenumber_types": get_contactable_type_ids_for_contactable(non_pref_phonenumber),
            "phonenumber_set-1-id": str(non_pref_phonenumber.id),
        }

        formset = ContactPhoneNumberFormSet(data=data, instance=self.contact)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(1, PhoneNumber.objects.count())
        self.assertFalse(PhoneNumber.objects.filter(number=non_pref_phonenumber.number).exists())

    def test_delete_preferred_unsuccessful_if_no_replacement(self) -> None:
        """
        Test that when delete is selected on the 'preferred' PhoneNumber, form validation fails unless
        there is a newly selected 'preferred' PhoneNumber.
        """
        pref_phonenumber = self._create_phonenumber(pref=True)
        non_pref_phonenumber = self._create_phonenumber(pref=False)

        data = {
            **self._get_management_form_data(initial=2),

            "phonenumber_set-0-archived": False,
            "phonenumber_set-0-contact": str(self.contact.id),
            "phonenumber_set-0-DELETE": True,
            "phonenumber_set-0-number_0": pref_phonenumber.country_code,
            "phonenumber_set-0-number_1": pref_phonenumber.national_number,
            "phonenumber_set-0-phonenumber_types": get_contactable_type_ids_for_contactable(pref_phonenumber),
            "phonenumber_set-0-id": str(pref_phonenumber.id),
            
            "phonenumber_set-1-archived": False,
            "phonenumber_set-1-contact": str(self.contact.id),
            "phonenumber_set-1-number_0": non_pref_phonenumber.country_code,
            "phonenumber_set-1-number_1": non_pref_phonenumber.national_number,
            "phonenumber_set-1-phonenumber_types": get_contactable_type_ids_for_contactable(non_pref_phonenumber),
            "phonenumber_set-1-id": str(non_pref_phonenumber.id),
        }

        formset = ContactPhoneNumberFormSet(data=data, instance=self.contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_with_multiple_preferred_phonenumbers(self) -> None:
        """
        Test that form validation fails if more than one PhoneNumber in the formset is set as PhoneNumberType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-contact": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7783444445",
            "phonenumber_set-0-phonenumber_types": [self.pref_type.id, self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-contact": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "4249998888",
            "phonenumber_set-1-phonenumber_types": [self.pref_type.id, self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = ContactPhoneNumberFormSet(data=data, instance=self.contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("Only one may be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_without_preferred_phonenumber_when_unarchived(self) -> None:
        """
        Test that form validation fails if no PhoneNumber in the formset is set as PhoneNumberType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-contact": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7783444445",
            "phonenumber_set-0-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-contact": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "4249998888",
            "phonenumber_set-1-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = ContactPhoneNumberFormSet(data=data, instance=self.contact)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that formset validation is successful with valid data and PhoneNumbers are successfully saved to db
        when PhoneNumbers are unarchived.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-contact": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7783444445",
            "phonenumber_set-0-phonenumber_types": [self.pref_type.id, self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-contact": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "4249998888",
            "phonenumber_set-1-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = ContactPhoneNumberFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = ContactFactory.create()
        formset.save()

        self.assertEqual(PhoneNumber.objects.all().count(), 2)
        
        pref_phonenumber_query = PhoneNumber.objects.filter(number="+447783444445")
        self.assertTrue(pref_phonenumber_query.exists())

        pref_phonenumber = pref_phonenumber_query.first()
        self.assertFalse(pref_phonenumber.archived)
        self.assertEqual(
            Counter([self.pref_type.id, self.non_pref_type.id]),
            Counter(pref_phonenumber.phonenumber_types.values_list("id", flat=True))
        )
        
        secondary_phonenumber_query = PhoneNumber.objects.filter(number="+14249998888")
        self.assertTrue(secondary_phonenumber_query.exists())

        secondary_phonenumber = secondary_phonenumber_query.first()
        self.assertFalse(secondary_phonenumber.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(secondary_phonenumber.phonenumber_types.values_list("id", flat=True))
        )

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that formset validation is successful with valid data and PhoneNumbers are successfully saved to db
        when all PhoneNumbers are archived - ensure that despite not having any 'preferred' PhoneNumber, validation and
        save is still successful.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-archived": True,
            "phonenumber_set-0-contact": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7711222333",
            "phonenumber_set-0-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-archived": True,
            "phonenumber_set-1-contact": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "2015550123",
            "phonenumber_set-1-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = ContactPhoneNumberFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = ContactFactory.create()
        formset.save()

        self.assertEqual(PhoneNumber.objects.all().count(), 2)
        
        first_phonenumber_query = PhoneNumber.objects.filter(number="+447711222333")
        self.assertTrue(first_phonenumber_query.exists())

        first_phonenumber = first_phonenumber_query.first()
        self.assertTrue(first_phonenumber.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(first_phonenumber.phonenumber_types.values_list("id", flat=True))
        )
        
        second_phonenumber_query = PhoneNumber.objects.filter(number="+12015550123")
        self.assertTrue(second_phonenumber_query.exists())

        second_phonenumber = second_phonenumber_query.first()
        self.assertTrue(second_phonenumber.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(second_phonenumber.phonenumber_types.values_list("id", flat=True))
        )

    
class TestAddressPhoneNumberFormSet(BaseFormTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.address = AddressFactory.create(user=self.primary_user)
        self.pref_type = PhoneNumberType.objects.preferred().first()
        self.non_pref_types = PhoneNumberType.objects.exclude(pk=self.pref_type.id).order_by("?")
        self.non_pref_type = self.non_pref_types.first()

    def _create_phonenumber(self, pref: bool, address: Optional[Address] = None):
        """
        Create a PhoneNumber for a provided Address (or not); optionally make it the preferred PhoneNumber.
        """
        if pref:
            phonenumber_types = [self.pref_type, self.non_pref_type]
        else:
            phonenumber_types = self.non_pref_types[:2]
        return AddressPhoneNumberFactory.create(
            address=address or self.address,
            phonenumber_types=phonenumber_types
        )
    
    def _get_management_form_data(self, initial: Optional[int] = 0, total: int = 2):
        """
        Create management form data for a PhoneNumber FormSet.
        """
        return {
            "phonenumber_set-TOTAL_FORMS": str(total),
            "phonenumber_set-INITIAL_FORMS": str(initial),
            "phonenumber_set-MIN_NUM_FORMS": "0",
            "phonenumber_set-MAX_NUM_FORMS": "1000",
        }

    def test_delete_present(self) -> None:
        """
        Test that the delete fields are present.
        """
        formset = AddressPhoneNumberFormSet(instance=self.address)
        for form in formset.forms:
            self.assertIn("DELETE", form.fields)

    def test_delete_successful(self) -> None:
        """
        Test that when delete is selected, the PhoneNumber is successfully deleted from db.
        """
        pref_phonenumber = self._create_phonenumber(pref=True)
        non_pref_phonenumber = self._create_phonenumber(pref=False)

        data = {
            **self._get_management_form_data(initial=2),

            "phonenumber_set-0-address": str(self.address.id),
            "phonenumber_set-0-archived": False,
            "phonenumber_set-0-number_0": pref_phonenumber.country_code,
            "phonenumber_set-0-number_1": pref_phonenumber.national_number,
            "phonenumber_set-0-phonenumber_types": get_contactable_type_ids_for_contactable(pref_phonenumber),
            "phonenumber_set-0-id": str(pref_phonenumber.id),
            
            "phonenumber_set-1-address": str(self.address.id),
            "phonenumber_set-1-archived": False,
            "phonenumber_set-1-DELETE": True,
            "phonenumber_set-1-number_0": non_pref_phonenumber.country_code,
            "phonenumber_set-1-number_1": non_pref_phonenumber.national_number,
            "phonenumber_set-1-phonenumber_types": get_contactable_type_ids_for_contactable(non_pref_phonenumber),
            "phonenumber_set-1-id": str(non_pref_phonenumber.id),
        }

        formset = AddressPhoneNumberFormSet(data=data, instance=self.address)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(1, PhoneNumber.objects.count())
        self.assertFalse(PhoneNumber.objects.filter(number=non_pref_phonenumber.number).exists())

    def test_delete_preferred_unsuccessful_if_no_replacement(self) -> None:
        """
        Test that when delete is selected on the 'preferred' PhoneNumber, form validation fails unless
        there is a newly selected 'preferred' PhoneNumber.
        """
        pref_phonenumber = self._create_phonenumber(pref=True)
        non_pref_phonenumber = self._create_phonenumber(pref=False)

        data = {
            **self._get_management_form_data(initial=2),

            "phonenumber_set-0-address": str(self.address.id),
            "phonenumber_set-0-archived": False,
            "phonenumber_set-0-DELETE": True,
            "phonenumber_set-0-number_0": pref_phonenumber.country_code,
            "phonenumber_set-0-number_1": pref_phonenumber.national_number,
            "phonenumber_set-0-phonenumber_types": get_contactable_type_ids_for_contactable(pref_phonenumber),
            "phonenumber_set-0-id": str(pref_phonenumber.id),
            
            "phonenumber_set-1-address": str(self.address.id),
            "phonenumber_set-1-archived": False,
            "phonenumber_set-1-number_0": non_pref_phonenumber.country_code,
            "phonenumber_set-1-number_1": non_pref_phonenumber.national_number,
            "phonenumber_set-1-phonenumber_types": get_contactable_type_ids_for_contactable(non_pref_phonenumber),
            "phonenumber_set-1-id": str(non_pref_phonenumber.id),
        }

        formset = AddressPhoneNumberFormSet(data=data, instance=self.address)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_with_multiple_preferred_phonenumbers(self) -> None:
        """
        Test that form validation fails if more than one PhoneNumber in the formset is set as PhoneNumberType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-address": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7783444445",
            "phonenumber_set-0-phonenumber_types": [self.pref_type.id, self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-address": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "4249998888",
            "phonenumber_set-1-phonenumber_types": [self.pref_type.id, self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = AddressPhoneNumberFormSet(data=data, instance=self.address)
        self.assertFalse(formset.is_valid())
        self.assertIn("Only one may be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_without_preferred_phonenumber_when_unarchived(self) -> None:
        """
        Test that form validation fails if no PhoneNumber in the formset is set as PhoneNumberType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-address": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7783444445",
            "phonenumber_set-0-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-address": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "4249998888",
            "phonenumber_set-1-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = AddressPhoneNumberFormSet(data=data, instance=self.address)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that formset validation is successful with valid data and PhoneNumbers are successfully saved to db
        when PhoneNumbers are unarchived.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-address": "",
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7783444445",
            "phonenumber_set-0-phonenumber_types": [self.pref_type.id, self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-address": "",
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "4249998888",
            "phonenumber_set-1-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = AddressPhoneNumberFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = AddressFactory.create()
        formset.save()

        self.assertEqual(PhoneNumber.objects.all().count(), 2)
        
        pref_phonenumber_query = PhoneNumber.objects.filter(number="+447783444445")
        self.assertTrue(pref_phonenumber_query.exists())

        pref_phonenumber = pref_phonenumber_query.first()
        self.assertFalse(pref_phonenumber.archived)
        self.assertEqual(
            Counter([self.pref_type.id, self.non_pref_type.id]),
            Counter(pref_phonenumber.phonenumber_types.values_list("id", flat=True))
        )
        
        secondary_phonenumber_query = PhoneNumber.objects.filter(number="+14249998888")
        self.assertTrue(secondary_phonenumber_query.exists())

        secondary_phonenumber = secondary_phonenumber_query.first()
        self.assertFalse(secondary_phonenumber.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(secondary_phonenumber.phonenumber_types.values_list("id", flat=True))
        )

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that formset validation is successful with valid data and PhoneNumbers are successfully saved to db
        when all PhoneNumbers are archived - ensure that despite not having any 'preferred' PhoneNumber, validation and
        save is still successful.
        """
        data = {
            **self._get_management_form_data(),

            "phonenumber_set-0-address": "",
            "phonenumber_set-0-archived": True,
            "phonenumber_set-0-number_0": "GB",
            "phonenumber_set-0-number_1": "7711222333",
            "phonenumber_set-0-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-0-id": "",
            
            "phonenumber_set-1-address": "",
            "phonenumber_set-1-archived": True,
            "phonenumber_set-1-number_0": "US",
            "phonenumber_set-1-number_1": "2015550123",
            "phonenumber_set-1-phonenumber_types": [self.non_pref_type.id],
            "phonenumber_set-1-id": "",
        }

        formset = AddressPhoneNumberFormSet(data=data)
        self.assertTrue(formset.is_valid())
        formset.instance = AddressFactory.create()
        formset.save()

        self.assertEqual(PhoneNumber.objects.all().count(), 2)
        
        first_phonenumber_query = PhoneNumber.objects.filter(number="+447711222333")
        self.assertTrue(first_phonenumber_query.exists())

        first_phonenumber = first_phonenumber_query.first()
        self.assertTrue(first_phonenumber.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(first_phonenumber.phonenumber_types.values_list("id", flat=True))
        )
        
        second_phonenumber_query = PhoneNumber.objects.filter(number="+12015550123")
        self.assertTrue(second_phonenumber_query.exists())

        second_phonenumber = second_phonenumber_query.first()
        self.assertTrue(second_phonenumber.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(second_phonenumber.phonenumber_types.values_list("id", flat=True))
        )

    
class TestTenancyFormSet(BaseFormTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.address_1 = AddressFactory.create(user=self.primary_user)
        self.address_2 = AddressFactory.create(user=self.primary_user)
        self.contact = ContactFactory.create(user=self.primary_user)
        self.pref_type = AddressType.objects.preferred().first()
        self.non_pref_types = AddressType.objects.exclude(pk=self.pref_type.id).order_by("?")
        self.non_pref_type = self.non_pref_types.first()

    def _create_tenancy(self, pref: bool, address: Address, contact: Optional[Contact] = None):
        """
        Create a Tenancy for a provided Address (or not); optionally make it the preferred Tenancy.
        """
        if pref:
            address_types = [self.pref_type, self.non_pref_type]
        else:
            address_types = self.non_pref_types[:2]
        tenancy = Tenancy.objects.create(
            address=address,
            contact=contact or self.contact,
        )
        tenancy.tenancy_types.set(address_types)
        return tenancy
    
    def _get_management_form_data(self, initial: Optional[int] = 0, total: int = 2):
        """
        Create management form data for a PhoneNumber FormSet.
        """
        return {
            "tenancy_set-TOTAL_FORMS": str(total),
            "tenancy_set-INITIAL_FORMS": str(initial),
            "tenancy_set-MIN_NUM_FORMS": "0",
            "tenancy_set-MAX_NUM_FORMS": "1000",
        }

    def test_delete_present(self) -> None:
        """
        Test that the delete fields are present.
        """
        formset = TenancyFormSet(instance=self.contact, user=self.primary_user)
        for form in formset.forms:
            self.assertIn("DELETE", form.fields)

    def test_delete_successful(self) -> None:
        """
        Test that when delete is selected, the Tenancy is successfully deleted from db.
        """
        pref_tenancy = self._create_tenancy(pref=True, address=self.address_1)
        non_pref_tenancy = self._create_tenancy(pref=False, address=self.address_2)

        data = {
            **self._get_management_form_data(initial=2),

            "tenancy_set-0-address": str(self.address_1.id),
            "tenancy_set-0-archived": False,
            "tenancy_set-0-tenancy_types": get_contactable_type_ids_for_contactable(pref_tenancy),
            "tenancy_set-0-id": str(pref_tenancy.id),
            
            "tenancy_set-1-address": str(self.address_2.id),
            "tenancy_set-1-archived": False,
            "tenancy_set-1-DELETE": True,
            "tenancy_set-1-tenancy_types": get_contactable_type_ids_for_contactable(non_pref_tenancy),
            "tenancy_set-1-id": str(non_pref_tenancy.id),
        }

        formset = TenancyFormSet(data=data, instance=self.contact, user=self.primary_user)
        self.assertTrue(formset.is_valid())
        formset.save()
        self.assertEqual(1, Tenancy.objects.count())
        self.assertFalse(Tenancy.objects.filter(pk=non_pref_tenancy.id).exists())

    def test_delete_preferred_unsuccessful_if_no_replacement(self) -> None:
        """
        Test that when delete is selected on the 'preferred' Tenancy, form validation fails unless
        there is a newly selected 'preferred' Tenancy.
        """
        pref_tenancy = self._create_tenancy(pref=True, address=self.address_1)
        non_pref_tenancy = self._create_tenancy(pref=False, address=self.address_2)

        data = {
            **self._get_management_form_data(initial=2),

            "tenancy_set-0-address": str(self.address_1.id),
            "tenancy_set-0-archived": False,
            "tenancy_set-0-DELETE": True,
            "tenancy_set-0-tenancy_types": get_contactable_type_ids_for_contactable(pref_tenancy),
            "tenancy_set-0-id": str(pref_tenancy.id),
            
            "tenancy_set-1-address": str(self.address_2.id),
            "tenancy_set-1-archived": False,
            "tenancy_set-1-tenancy_types": get_contactable_type_ids_for_contactable(non_pref_tenancy),
            "tenancy_set-1-id": str(non_pref_tenancy.id),
        }

        formset = TenancyFormSet(data=data, instance=self.contact, user=self.primary_user)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_with_multiple_preferred_tenancies(self) -> None:
        """
        Test that form validation fails if more than one Tenancy in the formset is set as AddressType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "tenancy_set-0-address": str(self.address_1.id),
            "tenancy_set-0-tenancy_types": [self.pref_type.id, self.non_pref_type.id],
            "tenancy_set-0-id": "",
            
            "tenancy_set-1-address": str(self.address_2.id),
            "tenancy_set-1-tenancy_types": [self.pref_type.id, self.non_pref_type.id],
            "tenancy_set-1-id": "",
        }

        formset = TenancyFormSet(data=data, instance=self.contact, user=self.primary_user)
        self.assertFalse(formset.is_valid())
        self.assertIn("Only one may be designated as 'preferred'.", formset.non_form_errors())

    def test_not_validates_without_preferred_tenancy_when_unarchived(self) -> None:
        """
        Test that form validation fails if no Tenancy in the formset is set as AddressType, 'preferred'.
        """
        data = {
            **self._get_management_form_data(),

            "tenancy_set-0-address": str(self.address_1.id),
            "tenancy_set-0-tenancy_types": [self.non_pref_type.id],
            "tenancy_set-0-id": "",
            
            "tenancy_set-1-address": str(self.address_2.id),
            "tenancy_set-1-tenancy_types": [self.non_pref_type.id],
            "tenancy_set-1-id": "",
        }

        formset = TenancyFormSet(data=data, instance=self.contact, user=self.primary_user)
        self.assertFalse(formset.is_valid())
        self.assertIn("One must be designated as 'preferred'.", formset.non_form_errors())

    def test_validates_and_saves_with_comprehensive_valid_data_unarchived(self) -> None:
        """
        Test that formset validation is successful with valid data and Tenancies are successfully saved to db
        when Tenancies are unarchived.
        """
        data = {
            **self._get_management_form_data(),

            "tenancy_set-0-address": str(self.address_1.id),
            "tenancy_set-0-tenancy_types": [self.pref_type.id, self.non_pref_type.id],
            "tenancy_set-0-id": "",
            
            "tenancy_set-1-address": str(self.address_2.id),
            "tenancy_set-1-tenancy_types": [self.non_pref_type.id],
            "tenancy_set-1-id": "",
        }

        formset = TenancyFormSet(data=data, user=self.primary_user)
        self.assertTrue(formset.is_valid())
        formset.instance = self.contact
        formset.save()

        self.assertEqual(Tenancy.objects.all().count(), 2)
        
        pref_tenancy_query = Tenancy.objects.filter(address=self.address_1.id)
        self.assertTrue(pref_tenancy_query.exists())

        pref_tenancy = pref_tenancy_query.first()
        self.assertFalse(pref_tenancy.archived)
        self.assertEqual(
            Counter([self.pref_type.id, self.non_pref_type.id]),
            Counter(pref_tenancy.tenancy_types.values_list("id", flat=True))
        )
        
        secondary_tenancy_query = Tenancy.objects.filter(address=self.address_2.id)
        self.assertTrue(secondary_tenancy_query.exists())

        secondary_tenancy = secondary_tenancy_query.first()
        self.assertFalse(secondary_tenancy.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(secondary_tenancy.tenancy_types.values_list("id", flat=True))
        )

    def test_validates_and_saves_with_comprehensive_valid_data_archived(self) -> None:
        """
        Test that formset validation is successful with valid data and Tenancies are successfully saved to db
        when all Tenancies are archived - ensure that despite not having any 'preferred' Tenancy, validation and
        save is still successful.
        """
        data = {
            **self._get_management_form_data(),

            "tenancy_set-0-address": str(self.address_1.id),
            "tenancy_set-0-archived": True,
            "tenancy_set-0-tenancy_types": [self.non_pref_type.id],
            "tenancy_set-0-id": "",
            
            "tenancy_set-1-address": str(self.address_2.id),
            "tenancy_set-1-archived": True,
            "tenancy_set-1-tenancy_types": [self.non_pref_type.id],
            "tenancy_set-1-id": "",
        }

        formset = TenancyFormSet(data=data, user=self.primary_user)
        self.assertTrue(formset.is_valid())
        formset.instance = self.contact
        formset.save()

        self.assertEqual(Tenancy.objects.all().count(), 2)
        
        first_tenancy_query = Tenancy.objects.filter(address=self.address_1.id)
        self.assertTrue(first_tenancy_query.exists())

        first_tenancy = first_tenancy_query.first()
        self.assertTrue(first_tenancy.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(first_tenancy.tenancy_types.values_list("id", flat=True))
        )
        
        second_tenancy_query = Tenancy.objects.filter(address=self.address_2.id)
        self.assertTrue(second_tenancy_query.exists())

        second_tenancy = second_tenancy_query.first()
        self.assertTrue(second_tenancy.archived)
        self.assertEqual(
            Counter([self.non_pref_type.id]),
            Counter(second_tenancy.tenancy_types.values_list("id", flat=True))
        )