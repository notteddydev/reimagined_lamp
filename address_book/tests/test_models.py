import datetime
import random

from collections import Counter
from django.core.exceptions import ValidationError
from django.test import TestCase
from faker import Faker

from address_book.factories.contact_factories import ContactFactory
from address_book.factories.phonenumber_factories import ContactPhoneNumberFactory
from address_book.factories.email_factories import EmailFactory
from address_book.factories.tenancy_factories import TenancyFactory
from address_book.models import Email, PhoneNumber, Tenancy

fake = Faker()


class TestContactModel(TestCase):
    def _test_data_produces_expected_error_for_expected_field(self, contact_data: dict, errorfield_to_test: str, errormsg_to_check: str) -> None:
        """
        Common logic for checking that provided 'contact_data' raises a given error for a given field.
        """
        with self.assertRaises(ValidationError) as cm:
            ContactFactory.create(**contact_data)

        self.assertIn(errorfield_to_test, cm.exception.message_dict)
        self.assertIn(errormsg_to_check, cm.exception.message_dict[errorfield_to_test])

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


class TestArchiveableContactableQuerySet(TestCase):
    def setUp(self):
        self.archiveable_contactables = [
            (ContactPhoneNumberFactory, PhoneNumber,),
            (EmailFactory, Email,),
            (TenancyFactory, Tenancy,),
        ]

    def test_archived_unarchived_querying_for_model(self) -> None:
        """
        Test that the archived() and unarchived() methods on the Archiveable models filter
        as expected.
        """
        for ContactableFactory, ContactableModel in self.archiveable_contactables:
            archived_count = random.randint(1, 7)
            unarchived_count = random.randint(1, 7)

            contact = ContactFactory.create()
            archived_archiveablecontactable = ContactableFactory.create_batch(archived_count, **{
                "archived": True,
                "contact": contact,
            })
            unarchived_archiveablecontactable = ContactableFactory.create_batch(unarchived_count, **{
                "archived": False,
                "contact": contact,
            })

            archived_found_in_query = ContactableModel.objects.archived().all()
            unarchived_found_in_query = ContactableModel.objects.unarchived().all()

            self.assertEqual(archived_count, archived_found_in_query.count())
            self.assertEqual(unarchived_count, unarchived_found_in_query.count())

            self.assertEqual(
                Counter([ac.id for ac in archived_archiveablecontactable]),
                Counter(archived_found_in_query.values_list("id", flat=True))
            )
            self.assertEqual(
                Counter([ac.id for ac in unarchived_archiveablecontactable]),
                Counter(unarchived_found_in_query.values_list("id", flat=True))
            )

    def test_preferred_non_preferred_querying_for_model(self) -> None:
        """
        Test that the preferred() and unpreferred() methods on the Contactable models filter
        as expected.
        """
        for ContactableFactory, ContactableModel in self.archiveable_contactables:
            unpreferred_count = random.randint(1, 7)

            contact = ContactFactory.create()
            preferred_archiveable_contactable = ContactableFactory.create(**{
                "contact": contact,
            })
            unpreferred_archiveable_contactables = ContactableFactory.create_batch(unpreferred_count, **{
                "contact": contact,
            })

            preferred_found_in_query = ContactableModel.objects.preferred().all()
            unpreferred_found_in_query = ContactableModel.objects.unpreferred().all()

            self.assertEqual(1, preferred_found_in_query.count())
            self.assertEqual(unpreferred_count, unpreferred_found_in_query.count())
            
            self.assertEqual(preferred_archiveable_contactable.id, preferred_found_in_query.first().id)
            self.assertEqual(
                Counter([ac.id for ac in unpreferred_archiveable_contactables]),
                Counter(unpreferred_found_in_query.values_list("id", flat=True))
            )

    def test_combo_querying_for_model(self) -> None:
        """
        Test that the archived() and unarchived() methods and preferred() and unpreferred()
        methods work and chain on one another filtering the ArchiveableContactable models
        as expected.
        """
        for ContactableFactory, ContactableModel in self.archiveable_contactables:
            unpreferred_archived_count = random.randint(1, 7)
            unpreferred_unarchived_count = random.randint(1, 7)

            contact = ContactFactory.create()
            preferred = ContactableFactory.create(**{
                "contact": contact,
            })
            unpreferred_archived = ContactableFactory.create_batch(unpreferred_archived_count, **{
                "contact": contact,
                "archived": True,
            })
            unpreferred_unarchived = ContactableFactory.create_batch(unpreferred_unarchived_count, **{
                "contact": contact,
                "archived": False,
            })

            preferred_archived_found_in_query = ContactableModel.objects.preferred().archived().all()
            preferred_unarchived_found_in_query = ContactableModel.objects.preferred().unarchived().all()
            unpreferred_archived_found_in_query = ContactableModel.objects.unpreferred().archived().all()
            unpreferred_unarchived_found_in_query = ContactableModel.objects.unpreferred().unarchived().all()

            self.assertEqual(0, preferred_archived_found_in_query.count())
            self.assertEqual(1, preferred_unarchived_found_in_query.count())
            self.assertEqual(unpreferred_archived_count, unpreferred_archived_found_in_query.count())
            self.assertEqual(unpreferred_unarchived_count, unpreferred_unarchived_found_in_query.count())
            
            self.assertEqual(preferred.id, preferred_unarchived_found_in_query.first().id)
            self.assertEqual(
                Counter([ac.id for ac in unpreferred_archived]),
                Counter(unpreferred_archived_found_in_query.values_list("id", flat=True))
            )
            self.assertEqual(
                Counter([ac.id for ac in unpreferred_unarchived]),
                Counter(unpreferred_unarchived_found_in_query.values_list("id", flat=True))
            )