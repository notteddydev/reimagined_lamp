import random

from collections import Counter

from django.apps import apps
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.test import Client, TestCase
from django.urls import reverse
from faker import Faker

from typing import Any, Optional

from address_book.factories.address_factories import AddressFactory
from address_book.factories.contact_factories import ContactFactory
from address_book.factories.tag_factories import TagFactory
from address_book.factories.tenancy_factories import TenancyFactory
from address_book.factories.user_factories import UserFactory
from address_book.models import Address, Contact, Tag, Tenancy

fake = Faker()


def get_pref_contactable_type_id(contactable_type: str) -> int | None:
    """
    If there is no 'preferred' ContactableType, returns None. Otherwise, returns the ContactableType.id.
    """
    contactable_type = apps.get_model("address_book", contactable_type)
    contactable_type_id = contactable_type.objects.preferred().values_list("id", flat=True).first()

    return contactable_type_id


class BaseModelViewTestCase:
    def setUp(self):
        self.client = Client()
        self.other_user_password = "password2"
        self.other_user = UserFactory.create(password=self.other_user_password)
        self.primary_user_password = "password"
        self.primary_user = UserFactory.create(password=self.primary_user_password)

    def _login_user(self, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """
        Logs in a user with the username and password provided, if none are provided it defaults to the
        primary_user that has been set on the class.
        """
        self.client.login(
            username=username or self.primary_user.username,
            password=password or self.primary_user_password
        )

    def _login_user_and_get_get_response(
            self,
            url: Optional[str] = None,
            username: Optional[str] = None,
            password: Optional[str] = None
            ) -> HttpResponse:
        """
        Logs in a user and makes a get request to the url provided, if none is provided it defaults to the
        url that has been set on the class. Returns the resulting HttpResponse object.
        """
        self._login_user(username=username, password=password)
        response = self.client.get(url or self.url)
        return response

    def _login_user_and_get_post_response(
            self,
            url: Optional[str] = None,
            post_data: Optional[dict] = {},
            username: Optional[str] = None,
            password: Optional[str] = None, **kwargs: Any
            ) -> HttpResponse:
        """
        Logs in a user and makes a post request to the url provided, if none is provided it defaults to the
        url that has been set on the class. Returns the resulting HttpResponse object.
        """
        self._login_user(username=username, password=password)
        response = self.client.post(url or self.url, post_data, **kwargs)
        return response

    def test_get_request_redirects_if_not_logged_in(self):
        """
        Make sure that if a non logged in user makes a get request to a view which requires login,
        they are redirected to the login page.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def assert_view_renders_correct_template_and_context(
            self,
            response: HttpResponse,
            template: str,
            context_keys: tuple
            ) -> None:
        """
        Assert that the view response has the correct template and contains the expected context keys.

        :param response: The response object from the view.
        :param template_name: The name of the template that should be used.
        :param context_keys: A tuple of context keys that should be present in the response.
        """
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template)
        for context_key in context_keys:
            self.assertIn(context_key, response.context)


class BaseDeleteViewTestCase(BaseModelViewTestCase):
    def setUp(self):
        super().setUp()
        self.context_keys = ("object",)
        self.template = f"address_book/{self.model._meta.object_name.lower()}_confirm_delete.html"

    def test_get(self):
        """
        Test that the DeleteView renders the expected template and provides the expected keys
        for the context object.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys,
        )

    def test_error_code_if_user_not_owner(self):
        """
        Make sure that if a Model is not owned by the logged in User, they are thrown the appropriate error code.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password,
        )
        self.assertEqual(response.status_code, self.error_code)

    def test_404_if_object_not_exists(self):
        """
        Make sure that if a Model does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        response = self._login_user_and_get_get_response(
            url=reverse(f"{self.model._meta.object_name.lower()}-delete", args=[self.object.id + 1])
        )
        self.assertEqual(response.status_code, 404)


class TestAddressCreateView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.context_keys = ("form", "phonenumber_formset",)
        self.template = "address_book/address_form.html"
        self.url = reverse("address-create")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the address-create view. Assert that
        the forms initial value is empty.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual({}, response.context["form"].initial)

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate address-detail
        page for the appropriate address.
        """
        valid_form_data = {
            "address_line_1": "1 easily identifiable road",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 56,
            "notes": "Not a real address tbh",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        address = Address.objects.get(address_line_1="1 easily identifiable road")
        self.assertRedirects(response, reverse("address-detail", args=[address.id]))

    def test_post_with_valid_data_and_next_url_passed(self):
        """
        Test that posting valid data is successful and redirects to the appropriate url, passed in as
        a 'next' param.
        """
        valid_form_data = {
            "address_line_1": "1 easily identifiable road",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 56,
            "notes": "Not a real address tbh",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        contact = ContactFactory.create(user=self.primary_user)
        redirect_url = reverse("contact-update", args=[contact.id])
        response = self._login_user_and_get_post_response(
            url=f"{self.url}?next={redirect_url}",
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, redirect_url)

    def test_post_with_valid_data_not_logged_in(self):
        """
        Test that posting valid data is successful and redirects to the appropriate address-detail
        page for the appropriate address.
        """
        valid_form_data = {
            "address_line_1": "1 easily identifiable road",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 56,
            "notes": "Not a real address tbh",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, valid_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the address-create
        template again displaying errors.
        """
        invalid_form_data = {
            "address_line_1": "",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 99999,
            "notes": "Not a real address tbh",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": [""],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": ["GB"],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=invalid_form_data
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(
            Counter(["country"]),
            Counter(list(response.context["form"].errors.as_data()))
        )

        phonenumber_formset_errors = response.context["phonenumber_formset"].errors
        self.assertDictEqual(
            {"number": ["This field is required."]},
            phonenumber_formset_errors[0]
        )
        self.assertDictEqual(
            {
                "number": ["This field is required."],
                "phonenumber_types": ["This field is required."],
            },
            phonenumber_formset_errors[1]
        )


class TestAddressDeleteView(BaseDeleteViewTestCase, TestCase):
    model = Address

    def setUp(self):
        super().setUp()
        self.error_code = 404
        self.contact = ContactFactory.create(user=self.primary_user)
        self.object = AddressFactory.create(user=self.primary_user)
        self.contact.addresses.add(self.object)
        self.url = reverse("address-delete", args=[self.object.id])

    def test_redirect_upon_success(self):
        """
        Test that a successful delete post request redirects to 'contact-list'.
        """
        response = self._login_user_and_get_post_response()
        self.assertRedirects(response, reverse("contact-list"))


class TestAddressUpdateView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.address = AddressFactory.create(user=self.primary_user)
        self.context_keys = ("form", "object", "phonenumber_formset",)
        self.template = "address_book/address_form.html"
        self.url = reverse("address-update", args=[self.address.id])

    def test_403_if_not_owner(self):
        """
        Make sure that if a logged in user attempts to access the address-update view
        for an address they do not own, they are thrown a tasty 403. See how they like that.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(self.template)

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the address-update view.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(self.address.id, response.context["object"].id)

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate address-detail
        page for the appropriate address.
        """
        valid_form_data = {
            "address_line_1": "1 easily identifiable street",
            "address_line_2": "the penthouse",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 79,
            "notes": "Another fake address",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        address = Address.objects.get(address_line_1="1 easily identifiable street")
        self.assertRedirects(response, reverse("address-detail", args=[address.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the address-update
        template again displaying errors.
        """
        invalid_form_data = {
            "address_line_1": "",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": "",
            "notes": "Not a real address tbh",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": [""],
            "phonenumber_set-0-number_1": ["7777112233"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": ["GB"],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=invalid_form_data
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(
            Counter(["city", "country"]),
            Counter(list(response.context["form"].errors.as_data()))
        )

        phonenumber_formset_errors = response.context["phonenumber_formset"].errors
        self.assertDictEqual(
            {"number": ["This field is required."]},
            phonenumber_formset_errors[0]
        )
        self.assertDictEqual(
            {
                "number": ["This field is required."],
                "phonenumber_types": ["This field is required."],
            },
            phonenumber_formset_errors[1]
        )

    def test_post_with_valid_data_not_owner(self):
        """
        Test that posting valid data as another user is unsuccessful and throws
        a tasty 403.
        """
        valid_form_data = {
            "address_line_1": "1 easily identifiable street",
            "address_line_2": "the penthouse",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 79,
            "notes": "Another fake address",
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data,
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, self.template)


class TestContactCreateView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.context_keys = ("email_formset", "form", "phonenumber_formset",
                             "tenancy_formset", "walletaddress_formset",)
        self.template = "address_book/contact_form.html"
        self.url = reverse("contact-create")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the contact-create view.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate contact-detail
        page for the appropriate contact.
        """
        address = AddressFactory.create(user=self.primary_user)

        valid_form_data = {
            "first_name": ["Jack"],
            "middle_names": ["Superbly fantastical identifiable middle names"],
            "last_name": ["Dee"],
            "nickname": [""],
            "gender": ["m"],
            "dob_month": [""],
            "dob_day": [""],
            "dob_year": [""],
            "dod_month": [""],
            "dod_day": [""],
            "dod_year": [""],
            "anniversary_month": [""],
            "anniversary_day": [""],
            "anniversary_year": [""],
            "year_met": ["2024"],
            "profession": [9],
            "website": [""],
            "notes": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": ["jack@dee.com"],
            "email_set-0-email_types": ["1", str(get_pref_contactable_type_id("EmailType"))],
            "email_set-0-id": [""],
            "email_set-0-contact": [""],
            "phonenumber_set-TOTAL_FORMS": ["1", "1"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777999000"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "tenancy_set-TOTAL_FORMS": ["1", "1"],
            "tenancy_set-INITIAL_FORMS": ["0", "0"],
            "tenancy_set-MIN_NUM_FORMS": ["0", "0"],
            "tenancy_set-MAX_NUM_FORMS": ["1000", "1000"],
            "tenancy_set-0-address": [str(address.id)],
            "tenancy_set-0-tenancy_types": ["1", str(get_pref_contactable_type_id("AddressType"))],
            "tenancy_set-0-id": [""],
            "tenancy_set-0-contact": [""],
            "walletaddress_set-TOTAL_FORMS": ["1", "1"],
            "walletaddress_set-INITIAL_FORMS": ["0", "0"],
            "walletaddress_set-MIN_NUM_FORMS": ["0", "0"],
            "walletaddress_set-MAX_NUM_FORMS": ["1000", "1000"],
            "walletaddress_set-0-network": [""],
            "walletaddress_set-0-transmission": [""],
            "walletaddress_set-0-address": [""],
            "walletaddress_set-0-id": [""],
            "walletaddress_set-0-contact": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        contact = Contact.objects.get(middle_names="Superbly fantastical identifiable middle names")
        self.assertRedirects(response, reverse("contact-detail", args=[contact.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the address-create
        template again displaying errors.
        """
        invalid_form_data = {
            "first_name": [""],
            "middle_names": ["Superbly fantastical identifiable middle names"],
            "last_name": ["Dee"],
            "nickname": [""],
            "gender": [""],
            "dob_month": [""],
            "dob_day": [""],
            "dob_year": [""],
            "dod_month": [""],
            "dod_day": [""],
            "dod_year": [""],
            "anniversary_month": [""],
            "anniversary_day": [""],
            "anniversary_year": [""],
            "year_met": [""],
            "profession": [9],
            "website": [""],
            "notes": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": [""],
            "email_set-0-email_types": ["1"],
            "email_set-0-id": [""],
            "email_set-0-contact": [""],
            "phonenumber_set-TOTAL_FORMS": ["1", "1"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": [""],
            "phonenumber_set-0-phonenumber_types": [str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "tenancy_set-TOTAL_FORMS": ["1", "1"],
            "tenancy_set-INITIAL_FORMS": ["0", "0"],
            "tenancy_set-MIN_NUM_FORMS": ["0", "0"],
            "tenancy_set-MAX_NUM_FORMS": ["1000", "1000"],
            "tenancy_set-0-address": [""],
            "tenancy_set-0-id": [""],
            "tenancy_set-0-contact": [""],
            "walletaddress_set-TOTAL_FORMS": ["1", "1"],
            "walletaddress_set-INITIAL_FORMS": ["0", "0"],
            "walletaddress_set-MIN_NUM_FORMS": ["0", "0"],
            "walletaddress_set-MAX_NUM_FORMS": ["1000", "1000"],
            "walletaddress_set-0-network": [""],
            "walletaddress_set-0-transmission": [""],
            "walletaddress_set-0-address": [""],
            "walletaddress_set-0-id": [""],
            "walletaddress_set-0-contact": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=invalid_form_data
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertTemplateUsed("address_book/address_form.html")  # TODO WHY THE F*@! is this coming out as true?
        self.assertEqual(
            Counter(["first_name", "gender", "year_met"]),
            Counter(list(response.context["form"].errors.as_data()))
        )
        self.assertDictEqual(
            {
                "number": ["This field is required."],
                "phonenumber_types": ["'Preferred' is not allowed as the only type."]
            },
            response.context["phonenumber_formset"].errors[0]
        )
        self.assertDictEqual(
            {"email": ["This field is required."]},
            response.context["email_formset"].errors[0]
        )
        self.assertIn("One must be designated as 'preferred'.", response.context["email_formset"].non_form_errors())


class TestContactDeleteView(BaseDeleteViewTestCase, TestCase):
    model = Contact

    def setUp(self):
        super().setUp()
        self.error_code = 404
        self.object = ContactFactory.create(user=self.primary_user)
        self.url = reverse("contact-delete", args=[self.object.id])

    def test_redirect_upon_success(self):
        """
        Test that a successful delete post request redirects to 'contact-list'.
        """
        response = self._login_user_and_get_post_response()
        self.assertRedirects(response, reverse("contact-list"))


class TestContactDetailView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.contact = ContactFactory.create(user=self.primary_user)
        self.context_keys = ("object",)
        self.template = "address_book/contact_detail.html"
        self.url = reverse("contact-detail", args=[self.contact.id])

    def test_view_url_exists_for_logged_in_user_who_owns_contact(self):
        """
        Make sure that if the owner is logged in and attempts to access the contact-detail
        view, they can do with success.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertContains(response, self.contact.full_name)
        self.assertEqual(self.contact.id, response.context["object"].id)

    def test_404_if_logged_in_as_other_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-detail view
        for a contact that does not belong to them, they are given a great big 404 right in their face.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 404)

    def test_404_if_contact_not_exists(self):
        """
        Make sure that if a Contact does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        response = self._login_user_and_get_get_response(
            url=reverse("contact-detail", args=[self.contact.id + 1])
        )
        self.assertEqual(response.status_code, 404)


class TestContactDownloadView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.contact = ContactFactory.create(user=self.primary_user)
        self.url = reverse("contact-download", args=[self.contact.id])

    def test_view_url_exists_for_logged_in_user_who_owns_contact(self):
        """
        Make sure that if the owner is logged in and attempts to access the contact-download view,
        they can do with success.
        """
        response = self._login_user_and_get_get_response()
        self.assertEqual(response.status_code, 200)

    def test_404_if_logged_in_as_other_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-download view
        for a contact that does not belong to them, they are given a great big 404 right in their face.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 404)

    def test_download_successful_if_logged_in_as_owner(self):
        """
        Make sure that if logged in as owner and Contact exists, image/png is returned.
        """
        response = self._login_user_and_get_get_response()
        self.assertEqual(response["Content-Type"], "text/vcard")
        self.assertEqual(
            response["Content-Disposition"],
            f"attachment; filename={slugify(self.contact.full_name)}.vcf"
        )

    def test_404_if_contact_not_exists(self):
        """
        Make sure that if a Contact does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        response = self._login_user_and_get_get_response(
            url=reverse("contact-download", args=[self.contact.id + 1])
        )
        self.assertEqual(response.status_code, 404)


class TestContactListDownloadView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("contact-list-download")

    def test_view_url_exists_for_logged_in_user_with_contacts(self):
        """
        Make sure that if a logged in user with contacts attempts to access the contact-list-download
        view, they can do with success.
        """
        ContactFactory.create(user=self.primary_user)
        response = self._login_user_and_get_get_response()
        self.assertEqual(response.status_code, 200)

    def test_successful_download_if_contacts_exist(self):
        """
        Make sure that if there are Contacts present, the response is a download.
        """
        ContactFactory.create(user=self.primary_user)
        response = self._login_user_and_get_get_response()
        self.assertIn("Content-Disposition", response)
        self.assertEqual(response["Content-Disposition"], "attachment; filename=contacts.vcf")
        self.assertEqual(response["Content-Type"], "text/vcard")

    def test_status_404_if_no_contacts(self):
        """
        Make sure there is a 404 status code if there are no Contacts listed.
        """
        response = self._login_user_and_get_get_response()
        self.assertEqual(response.status_code, 404)

    def test_other_user_contacts_not_present_in_download(self):
        """
        Make sure that if there are Contacts present for other users,
        they are not included in the download.
        """
        other_user_contact = ContactFactory.create(user=self.other_user)
        primary_user_contact = ContactFactory.create(user=self.primary_user)
        response = self._login_user_and_get_get_response()

        self.assertIn("Content-Disposition", response)
        self.assertEqual(response["Content-Disposition"], "attachment; filename=contacts.vcf")
        self.assertEqual(response["Content-Type"], "text/vcard")

        vcard_data = response.content.decode("utf-8")
        self.assertIn(primary_user_contact.full_name, vcard_data)
        self.assertNotIn(other_user_contact.full_name, vcard_data)


class TestContactListView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.context_keys = ("filter_formset", "object_list",)
        self.template = "address_book/contact_list.html"
        self.url = reverse("contact-list")

    def test_view_renders_correct_template_and_context_and_user_contact_appears_in_response(self):
        """
        Test that the view for a logged in user returns the contact_list.html template,
        that the Download List button appears if Contacts are found for the list, and that
        any User Contacts are rendered in the response.
        """
        contact = ContactFactory.create(user=self.primary_user)
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertContains(response, "Download List")
        self.assertIn(contact, response.context["object_list"])
        self.assertContains(response, contact)

    def test_view_handles_no_contacts(self):
        """
        Make sure that an empty object_list is returned when no contacts are found,
        and that the 'Download List' button is hidden from the template.
        """
        response = self._login_user_and_get_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["object_list"], [])
        self.assertNotContains(response, "Download List")

    def test_other_users_contacts_not_present_in_context_data(self):
        """
        Make sure that Contacts belonging to another User are not present in the contexts
        object_list.
        """
        ContactFactory.create(user=self.other_user)
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertQuerySetEqual(response.context["object_list"], [])


class TestContactQrCodeView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.contact = ContactFactory.create(user=self.primary_user)
        self.url = reverse("contact-qrcode", args=[self.contact.id])

    def test_view_url_exists_for_logged_in_user_who_owns_contact(self):
        """
        Make sure that if the owner is logged in and attempts to access the contact-qrcode
        view, they can do with success.
        """
        response = self._login_user_and_get_get_response()
        self.assertEqual(response.status_code, 200)

    def test_404_if_logged_in_as_other_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-qrcode view
        for a contact that does not belong to them, they are given a great big 404 right in their face.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 404)

    def test_png_returned_if_logged_in_as_owner(self):
        """
        Make sure that if logged in as owner and Contact exists, image/png is returned.
        """
        response = self._login_user_and_get_get_response()
        self.assertEqual(response["Content-Type"], "image/png")

    def test_404_if_contact_not_exists(self):
        """
        Make sure that if a Contact does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        response = self._login_user_and_get_get_response(
            url=reverse("contact-qrcode", args=[self.contact.id + 1])
        )
        self.assertEqual(response.status_code, 404)


class TestContactUpdateView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.contact = ContactFactory.create(user=self.primary_user)
        self.context_keys = ("email_formset", "form", "object", "phonenumber_formset",
                             "tenancy_formset", "walletaddress_formset",)
        self.template = "address_book/contact_form.html"
        self.url = reverse("contact-update", args=[self.contact.id])

    def test_403_if_not_owner(self):
        """
        Make sure that if a logged in user attempts to access the contact-update view
        for a contact they do not own, they are thrown a tasty 403. See how they like that.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed("address_book/contact_form.html")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the contact-update view.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(self.contact.id, response.context["object"].id)

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate contact-detail
        page for the appropriate contact.
        """
        address = AddressFactory.create(user=self.primary_user)

        valid_form_data = {
            "first_name": ["Jack"],
            "middle_names": ["Superbly fantastical identifiable middle names"],
            "last_name": ["Dee"],
            "nickname": [""],
            "gender": ["m"],
            "dob_month": [""],
            "dob_day": [""],
            "dob_year": [""],
            "dod_month": [""],
            "dod_day": [""],
            "dod_year": [""],
            "anniversary_month": [""],
            "anniversary_day": [""],
            "anniversary_year": [""],
            "year_met": ["2024"],
            "profession": [9],
            "website": [""],
            "notes": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": ["jack@dee.com"],
            "email_set-0-email_types": ["1", str(get_pref_contactable_type_id("EmailType"))],
            "email_set-0-id": [""],
            "email_set-0-contact": [""],
            "phonenumber_set-TOTAL_FORMS": ["1", "1"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777999000"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "tenancy_set-TOTAL_FORMS": ["1", "1"],
            "tenancy_set-INITIAL_FORMS": ["0", "0"],
            "tenancy_set-MIN_NUM_FORMS": ["0", "0"],
            "tenancy_set-MAX_NUM_FORMS": ["1000", "1000"],
            "tenancy_set-0-address": [str(address.id)],
            "tenancy_set-0-tenancy_types": ["1", str(get_pref_contactable_type_id("AddressType"))],
            "tenancy_set-0-id": [""],
            "tenancy_set-0-contact": [""],
            "walletaddress_set-TOTAL_FORMS": ["1", "1"],
            "walletaddress_set-INITIAL_FORMS": ["0", "0"],
            "walletaddress_set-MIN_NUM_FORMS": ["0", "0"],
            "walletaddress_set-MAX_NUM_FORMS": ["1000", "1000"],
            "walletaddress_set-0-network": [""],
            "walletaddress_set-0-transmission": [""],
            "walletaddress_set-0-address": [""],
            "walletaddress_set-0-id": [""],
            "walletaddress_set-0-contact": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        contact = Contact.objects.get(middle_names="Superbly fantastical identifiable middle names")
        self.assertRedirects(response, reverse("contact-detail", args=[contact.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the contact-update
        template again displaying errors.
        """
        address = AddressFactory.create(user=self.primary_user)

        invalid_form_data = {
            "first_name": [""],
            "middle_names": ["Superbly fantastical identifiable middle names"],
            "last_name": ["Dee"],
            "nickname": [""],
            "gender": [""],
            "dob_month": [""],
            "dob_day": [""],
            "dob_year": [""],
            "dod_month": [""],
            "dod_day": [""],
            "dod_year": [""],
            "anniversary_month": [""],
            "anniversary_day": [""],
            "anniversary_year": [""],
            "year_met": [""],
            "profession": [9],
            "website": [""],
            "notes": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": [""],
            "email_set-0-email_types": ["1"],
            "email_set-0-id": [""],
            "email_set-0-contact": [""],
            "phonenumber_set-TOTAL_FORMS": ["1", "1"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": [""],
            "phonenumber_set-0-phonenumber_types": [str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "tenancy_set-TOTAL_FORMS": ["2", "2"],
            "tenancy_set-INITIAL_FORMS": ["0", "0"],
            "tenancy_set-MIN_NUM_FORMS": ["0", "0"],
            "tenancy_set-MAX_NUM_FORMS": ["1000", "1000"],
            "tenancy_set-0-address": [str(address.id)],
            "tenancy_set-0-tenancy_types": ["1", str(get_pref_contactable_type_id("AddressType"))],
            "tenancy_set-0-id": [""],
            "tenancy_set-0-contact": [""],
            "tenancy_set-1-address": [str(address.id)],
            "tenancy_set-1-tenancy_types": ["3", str(get_pref_contactable_type_id("AddressType"))],
            "tenancy_set-1-id": [""],
            "tenancy_set-1-contact": [""],
            "walletaddress_set-TOTAL_FORMS": ["1", "1"],
            "walletaddress_set-INITIAL_FORMS": ["0", "0"],
            "walletaddress_set-MIN_NUM_FORMS": ["0", "0"],
            "walletaddress_set-MAX_NUM_FORMS": ["1000", "1000"],
            "walletaddress_set-0-network": [""],
            "walletaddress_set-0-transmission": [""],
            "walletaddress_set-0-address": [""],
            "walletaddress_set-0-id": [""],
            "walletaddress_set-0-contact": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=invalid_form_data
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(
            Counter(["first_name", "gender", "year_met"]),
            Counter(list(response.context["form"].errors.as_data()))
        )
        self.assertDictEqual(
            {
                "number": ["This field is required."],
                "phonenumber_types": ["'Preferred' is not allowed as the only type."]
            },
            response.context["phonenumber_formset"].errors[0]
        )
        self.assertDictEqual(
            {"email": ["This field is required."]},
            response.context["email_formset"].errors[0]
        )
        self.assertIn("One must be designated as 'preferred'.", response.context["email_formset"].non_form_errors())
        self.assertIn(
            "Only one may be designated as 'preferred'.",
            response.context["tenancy_formset"].non_form_errors()
        )
        self.assertIn(
            "An address may only be assigned to a contact once.",
            response.context["tenancy_formset"].non_form_errors()
        )

    def test_post_with_valid_data_not_owner(self):
        """
        Test that posting valid data as another user is unsuccessful and throws
        a tasty 403.
        """
        valid_form_data = {
            "first_name": ["Jack"],
            "middle_names": ["Superbly fantastical identifiable middle names"],
            "last_name": ["Dee"],
            "nickname": [""],
            "gender": ["m"],
            "dob_month": [""],
            "dob_day": [""],
            "dob_year": [""],
            "dod_month": [""],
            "dod_day": [""],
            "dod_year": [""],
            "anniversary_month": [""],
            "anniversary_day": [""],
            "anniversary_year": [""],
            "year_met": ["2024"],
            "profession": [9],
            "website": [""],
            "notes": [""],
            "phonenumber_set-TOTAL_FORMS": ["1", "1"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777999000"],
            "phonenumber_set-0-phonenumber_types": ["1", str(get_pref_contactable_type_id("PhonenumberType"))],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": ["jack@dee.com"],
            "email_set-0-email_types": ["1", str(get_pref_contactable_type_id("EmailType"))],
            "email_set-0-id": [""],
            "email_set-0-contact": [""],
            "walletaddress_set-TOTAL_FORMS": ["1", "1"],
            "walletaddress_set-INITIAL_FORMS": ["0", "0"],
            "walletaddress_set-MIN_NUM_FORMS": ["0", "0"],
            "walletaddress_set-MAX_NUM_FORMS": ["1000", "1000"],
            "walletaddress_set-0-network": [""],
            "walletaddress_set-0-transmission": [""],
            "walletaddress_set-0-address": [""],
            "walletaddress_set-0-id": [""],
            "walletaddress_set-0-contact": [""]
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data,
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, self.template)


class TestTagCreateView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.context_keys = ("form",)
        self.template = "address_book/tag_form.html"
        self.url = reverse("tag-create")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the tag-create view. Assert that
        the forms initial value is empty.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual({}, response.context["form"].initial)

    def test_get_view_with_invalid_contact_id_param_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the tag-create view. Assert that
        the forms initial value is empty.
        """
        response = self._login_user_and_get_get_response(
            url=f"{self.url}?contact_id=23"
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual({}, response.context["form"].initial)

    def test_get_view_with_valid_contact_id_param_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the tag-create view. Assert that
        the forms initial value contains the valid contact_id passed in params, and that
        the associated contact comes preselected in the multiple choice menu.
        """
        contact = ContactFactory.create(user=self.primary_user)
        response = self._login_user_and_get_get_response(
            url=f"{self.url}?contact_id={contact.id}"
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )

        initial_form_data = response.context["form"].initial
        self.assertIn("contacts", initial_form_data)
        self.assertEqual(1, len(initial_form_data.get("contacts")))
        self.assertEqual(contact.id, initial_form_data.get("contacts")[0])
        self.assertContains(
            response,
            f'<input type="checkbox" name="contacts" value="{contact.id}" id="id_contacts_0" checked>\n {contact}'
        )

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the contact-list page,
        with no contact_id in the HTTP_REFERER, and not referring from the TagCreate 'get' url.
        """
        contact = ContactFactory.create(user=self.primary_user)
        valid_form_data = {
            "name": "Supercalafragalistically unique tag name",
            "contacts": [contact.id],
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("contact-list"))

    def test_post_with_valid_data_and_contact_id_and_next_get_params(self):
        """
        Test that posting valid data is successful and redirects to the contact-detail page
        for the Contact that referred to the TagCreate page.
        """
        contact = ContactFactory.create(user=self.primary_user)
        valid_form_data = {
            "name": "Supercalafragalistically unique tag name",
            "contacts": [contact.id],
        }
        response = self._login_user_and_get_post_response(
            url=f"{self.url}?contact_id={contact.id}&next={reverse('contact-detail', args=[contact.id])}",
            post_data=valid_form_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("contact-detail", args=[contact.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the tag-create
        template again displaying errors.
        """
        invalid_form_data = {
            "name": "This name is longer than 50 chars. This name is \
                longer than 50 chars. This name is longer than 50 chars."
        }
        response = self._login_user_and_get_post_response(
            post_data=invalid_form_data
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(
            Counter(["name", "contacts"]),
            Counter(list(response.context["form"].errors.as_data()))
        )


class TestTagDeleteView(BaseDeleteViewTestCase, TestCase):
    model = Tag

    def setUp(self):
        super().setUp()
        self.error_code = 404
        self.contact = ContactFactory.create(user=self.primary_user)
        self.object = TagFactory.create(user=self.primary_user)
        self.contact.tags.add(self.object)
        self.url = reverse("tag-delete", args=[self.object.id])

    def test_redirect_upon_success_no_contact_id(self):
        """
        Test that a successful delete post request redirects to 'contact-list' when
        there is no contact_id get param.
        """
        response = self._login_user_and_get_post_response()
        self.assertRedirects(response, reverse("contact-list"))

    def test_redirect_upon_success_with_contact_id(self):
        """
        Test that a successful delete post request redirects to 'contact-detail' when
        there is a contact_id get param.
        """
        next_url = reverse("contact-detail", args=[self.contact.id])
        url = f"{reverse('tag-delete', args=[self.object.id])}?next={next_url}"
        response = self._login_user_and_get_post_response(
            url=url
        )
        self.assertRedirects(response, reverse("contact-detail", args=[self.contact.id]))


class TestTagUpdateView(BaseModelViewTestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.tag = TagFactory.create(name="Is a silly billy", user=self.primary_user)
        self.context_keys = ("form", "object",)
        self.template = "address_book/tag_form.html"
        self.url = reverse("tag-update", args=[self.tag.id])

    def test_403_if_not_owner(self):
        """
        Make sure that if a logged in user attempts to access the tag-update view
        for a tag they do not own, they are thrown a tasty 403. See how they like that.
        """
        response = self._login_user_and_get_get_response(
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed("address_book/tag_form.html")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the tag-update view.
        """
        response = self._login_user_and_get_get_response()
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(self.tag.id, response.context["object"].id)

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate contact-list page.
        """
        contacts = ContactFactory.create_batch(7, user=self.primary_user)
        selected_contact_ids = [contact.id for contact in contacts[:random.randint(1, 6)]]

        valid_form_data = {
            "name": "Cries all the time",
            "contacts": selected_contact_ids,
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tag.objects.filter(name="Cries all the time").exists())
        self.assertFalse(Tag.objects.filter(name="Is a silly billy").exists())
        self.assertEqual(
            Counter(selected_contact_ids),
            Counter(Contact.objects.filter(tags__name="Cries all the time").values_list("id", flat=True)),
        )
        self.assertRedirects(response, reverse("contact-list"))

    def test_post_with_valid_data_and_next_get_param(self):
        """
        Test that posting valid data is successful and redirects to the appropriate contact-detail page.
        """
        contacts = ContactFactory.create_batch(7, user=self.primary_user)
        selected_contact_ids = [contact.id for contact in contacts[:random.randint(1, 6)]]
        referred_from_contact_id = contacts[random.randint(0, 6)].id

        valid_form_data = {
            "name": "Cries all the time",
            "contacts": selected_contact_ids,
        }
        response = self._login_user_and_get_post_response(
            url=f"{self.url}?next={reverse('contact-detail', args=[referred_from_contact_id])}",
            post_data=valid_form_data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tag.objects.filter(name="Cries all the time").exists())
        self.assertFalse(Tag.objects.filter(name="Is a silly billy").exists())
        self.assertEqual(
            Counter(selected_contact_ids),
            Counter(Contact.objects.filter(tags__name="Cries all the time").values_list("id", flat=True)),
        )
        self.assertRedirects(response, reverse("contact-detail", args=[referred_from_contact_id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the tag-update
        template again displaying errors.
        """
        other_contacts = ContactFactory.create_batch(4, user=self.other_user)

        invalid_form_data = {
            "name": "This string is longer than 50 characters deliberately so that it fails validation",
            "contacts": [contact.id for contact in other_contacts],
        }
        response = self._login_user_and_get_post_response(
            post_data=invalid_form_data
        )
        self.assert_view_renders_correct_template_and_context(
            response=response,
            template=self.template,
            context_keys=self.context_keys
        )
        self.assertEqual(
            Counter(["contacts", "name"]),
            Counter(list(response.context["form"].errors.as_data()))
        )

    def test_post_with_valid_data_not_owner(self):
        """
        Test that posting valid data as another user is unsuccessful and throws
        a tasty 403.
        """
        contacts = ContactFactory.create_batch(4, user=self.primary_user)
        valid_form_data = {
            "contacts": [contact.id for contact in contacts],
            "name": fake.word(),
        }
        response = self._login_user_and_get_post_response(
            post_data=valid_form_data,
            username=self.other_user.username,
            password=self.other_user_password
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, self.template)


class TestTenancyDeleteView(BaseDeleteViewTestCase, TestCase):
    model = Tenancy

    def setUp(self):
        super().setUp()
        self.error_code = 403
        self.contact = ContactFactory.create(user=self.primary_user)
        self.address = AddressFactory.create(user=self.primary_user)
        self.object = TenancyFactory.create(
            address=self.address,
            contact=self.contact,
        )
        self.url = reverse("tenancy-delete", args=[self.object.id])

    def test_redirect_upon_success(self):
        """
        Test that a successful delete post request redirects to 'address-detail'.
        """
        response = self._login_user_and_get_post_response()
        self.assertRedirects(response, reverse("address-detail", args=[self.address.id]))
