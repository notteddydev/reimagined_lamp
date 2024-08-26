from collections import Counter

from django.contrib.auth.models import User
from django.test import TestCase

from address_book.forms import AddressForm
from address_book.models import Address


class TestAddressForm(TestCase):
    def setUp(self) -> None:
        self.primary_user_password="password"
        self.primary_user = User.objects.create_user(
            username="tess_ting",
            email="tess@ting.com",
            password=self.primary_user_password
        )

    def test_form_init_with_user(self) -> None:
        """
        Test that the AddressForm is correctly initialised setting the user_id to the form instance.
        """
        form = AddressForm(self.primary_user)

        self.assertEqual(self.primary_user.id, form.instance.user_id)

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