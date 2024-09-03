import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from faker import Faker

from address_book.factories.contact_factories import ContactFactory

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