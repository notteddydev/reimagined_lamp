from collections import Counter
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.test import Client, TestCase
from django.urls import reverse

from address_book.constants import ADDRESS_TYPE__NAME_PREF, EMAIL_TYPE__NAME_PREF, PHONENUMBER_TYPE__NAME_PREF
from address_book.models import Address, AddressType, Contact, EmailType, PhoneNumberType

def get_pref_address_type_id(stringify=False):
    address_type = AddressType.objects.get(name=ADDRESS_TYPE__NAME_PREF)

    if not address_type.id:
        return None

    return str(address_type.id) if stringify else address_type.id

def get_pref_email_type_id(stringify=False):
    email_type = EmailType.objects.get(name=EMAIL_TYPE__NAME_PREF)

    if not email_type.id:
        return None

    return str(email_type.id) if stringify else email_type.id

def get_pref_phonenumber_type_id(stringify=False):
    phonenumber_type = PhoneNumberType.objects.get(name=PHONENUMBER_TYPE__NAME_PREF)

    if not phonenumber_type.id:
        return None

    return str(phonenumber_type.id) if stringify else phonenumber_type.id


class TestAddressCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.url = reverse("address-create")
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the address-create view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the address-create view. Assert that
        the forms initial value is empty.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/address_form.html")
        self.assertIn("form", response.context)
        self.assertIn("phonenumber_formset", response.context)
        self.assertEqual({}, response.context["form"].initial)

    def test_get_view_with_invalid_contact_id_param_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the address-create view. Assert that
        the forms initial value is empty.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(f"{self.url}?contact_id=23")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/address_form.html")
        self.assertIn("form", response.context)
        self.assertIn("phonenumber_formset", response.context)
        self.assertEqual({}, response.context["form"].initial)

    def test_get_view_with_valid_contact_id_param_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the address-create view. Assert that
        the forms initial value contains the valid contact_id passed in params, and that
        the associated contact comes preselected in the multiple choice menu.
        """
        contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(f"{self.url}?contact_id={contact.id}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/address_form.html")
        self.assertIn("phonenumber_formset", response.context)
        self.assertIn("form", response.context)

        initial_form_data = response.context["form"].initial
        self.assertIn("contacts", initial_form_data)
        self.assertEqual(1, len(initial_form_data.get("contacts")))
        self.assertEqual(contact.id, initial_form_data.get("contacts")[0])
        self.assertContains(response, f'<option value="{contact.id}" selected>{contact}')

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate address-detail
        page for the appropriate address.
        """
        self.client.login(username="tess_ting", password="password")
        contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        valid_form_data = {
            "address_line_1": "1 easily identifiable road",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 56,
            "notes": "Not a real address tbh",
            "contacts": [contact.id],
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, valid_form_data)
        self.assertEqual(response.status_code, 302)
        address = Address.objects.get(address_line_1="1 easily identifiable road")
        self.assertRedirects(response, reverse("address-detail", args=[address.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the address-create
        template again displaying errors.
        """
        self.client.login(username="tess_ting", password="password")
        invalid_form_data = {
            "address_line_1": "",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 99999,
            "notes": "Not a real address tbh",
            "contacts": [],
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": [""],
            "phonenumber_set-0-phonenumber_types": ["1", get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": ["GB"],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, invalid_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("address_book/address_form.html")
        self.assertIn("form", response.context)
        self.assertIn("phonenumber_formset", response.context)
        self.assertEqual(
            Counter(["address_line_1", "contacts", "country"]),
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


class TestAddressUpdateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.address = Address.objects.create(
            address_line_1="1 easily identifiable road",
            address_line_2="apartment 100",
            neighbourhood="Mayfair",
            city="London",
            state="London",
            postcode="SN1 8GB",
            country_id=56,
            notes="Not a real address tbh",
            user_id=self.user.id
        )
        self.url = reverse("address-update", args=[self.address.id])
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the address-update view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")
    
    def test_403_if_not_owner(self):
        """
        Make sure that if a logged in user attempts to access the address-update view
        for an address they do not own, they are thrown a tasty 403. See how they like that.
        """
        User.objects.create_user(email="tess@ting2.com", password="password", username="tess_ting2")
        self.client.login(username="tess_ting2", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed("adddress_book/address_form.html")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the address-update view.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/address_form.html")
        self.assertIn("form", response.context)
        self.assertIn("object", response.context)
        self.assertEqual(self.address.id, response.context["object"].id)
        self.assertIn("phonenumber_formset", response.context)

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate address-detail
        page for the appropriate address.
        """
        self.client.login(username="tess_ting", password="password")
        contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        valid_form_data = {
            "address_line_1": "1 easily identifiable street",
            "address_line_2": "the penthouse",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 79,
            "notes": "Another fake address",
            "contacts": [contact.id],
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, valid_form_data)
        self.assertEqual(response.status_code, 302)
        address = Address.objects.get(address_line_1="1 easily identifiable street")
        self.assertRedirects(response, reverse("address-detail", args=[address.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the address-update
        template again displaying errors.
        """
        self.client.login(username="tess_ting", password="password")
        invalid_form_data = {
            "address_line_1": "",
            "address_line_2": "apartment 100",
            "neighbourhood": "Mayfair",
            "city": "",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": "",
            "notes": "Not a real address tbh",
            "contacts": [],
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": [""],
            "phonenumber_set-0-number_1": ["7777112233"],
            "phonenumber_set-0-phonenumber_types": ["1", get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": ["GB"],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, invalid_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("address_book/address_form.html")
        self.assertIn("form", response.context)
        self.assertIn("phonenumber_formset", response.context)
        self.assertEqual(
            Counter(["address_line_1", "city", "contacts", "country"]),
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
        User.objects.create_user(username="tess_ting2", email="tess@ting2.com", password="password")
        self.client.login(username="tess_ting2", password="password")
        contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        valid_form_data = {
            "address_line_1": "1 easily identifiable street",
            "address_line_2": "the penthouse",
            "neighbourhood": "Mayfair",
            "city": "London",
            "state": "London",
            "postcode": "SN1 8GB",
            "country": 79,
            "notes": "Another fake address",
            "contacts": [contact.id],
            "phonenumber_set-TOTAL_FORMS": ["2", "2"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": ["7777111222"],
            "phonenumber_set-0-phonenumber_types": ["1", get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": [""],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, valid_form_data)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, "address_book/address_form.html")


class TestContactCreateView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.url = reverse("contact-create")
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the contact-create view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")

    def test_get_view_for_logged_in_user(self):
        """
        Test correct template is used and appropriate keys are passed to the context
        when a logged in user attempts to access the contact-create view.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/contact_form.html")
        self.assertIn("form", response.context)
        self.assertIn("email_formset", response.context)
        self.assertIn("phonenumber_formset", response.context)
        self.assertIn("walletaddress_formset", response.context)

    def test_post_with_valid_data(self):
        """
        Test that posting valid data is successful and redirects to the appropriate contact-detail
        page for the appropriate contact.
        """
        self.client.login(username="tess_ting", password="password")
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
            "phonenumber_set-0-phonenumber_types": ["1", get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": ["jack@dee.com"],
            "email_set-0-email_types": ["1", get_pref_email_type_id(stringify=True)],
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
        response = self.client.post(self.url, valid_form_data)
        self.assertEqual(response.status_code, 302)
        contact = Contact.objects.get(middle_names="Superbly fantastical identifiable middle names")
        self.assertRedirects(response, reverse("contact-detail", args=[contact.id]))

    def test_post_with_invalid_data(self):
        """
        Test that posting invalid data is unsuccessful and renders the address-create
        template again displaying errors.
        """
        self.client.login(username="tess_ting", password="password")
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
            "phonenumber_set-TOTAL_FORMS": ["1", "1"],
            "phonenumber_set-INITIAL_FORMS": ["0", "0"],
            "phonenumber_set-MIN_NUM_FORMS": ["0", "0"],
            "phonenumber_set-MAX_NUM_FORMS": ["1000", "1000"],
            "phonenumber_set-0-number_0": ["GB"],
            "phonenumber_set-0-number_1": [""],
            "phonenumber_set-0-phonenumber_types": [get_pref_phonenumber_type_id(stringify=True)],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-contact": [""],
            "email_set-TOTAL_FORMS": ["1", "1"],
            "email_set-INITIAL_FORMS": ["0", "0"],
            "email_set-MIN_NUM_FORMS": ["0", "0"],
            "email_set-MAX_NUM_FORMS": ["1000", "1000"],
            "email_set-0-email": [""],
            "email_set-0-email_types": ["1"],
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
        response = self.client.post(self.url, invalid_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("address_book/address_form.html")
        self.assertIn("form", response.context)
        self.assertIn("email_formset", response.context)
        self.assertIn("phonenumber_formset", response.context)
        self.assertIn("walletaddress_formset", response.context)
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
        self.assertIn("One email must be designated as 'preferred'.", response.context["email_formset"].non_form_errors())


class TestContactDetailView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        self.url = reverse("contact-detail", args=[self.contact.id])

    def _login_and_get_response(self):
        """
        Logs the user in, attempts to access the contact-detail view, and returns the response.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        return response

    def test_view_url_exists_for_logged_in_user_who_owns_contact(self):
        """
        Make sure that if the owner is logged in and attempts to access the contact-detail
        view, they can do with success.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("address_book/contact_detail.html")
        self.assertContains(response, self.contact.full_name)
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the contact-detail view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")
    
    def test_404_if_logged_in_as_other_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-detail view
        for a contact that does not belong to them, they are given a great big 404 right in their face. 
        """
        User.objects.create_user(username="tess_ting2", email="tess@ting2.com", password="password")
        self.client.login(username="tess_ting2", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_404_if_contact_not_exists(self):
        """
        Make sure that if a Contact does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(reverse("contact-detail", args=[self.contact.id + 1]))
        self.assertEqual(response.status_code, 404)


class TestContactDownloadView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        self.url = reverse("contact-download", args=[self.contact.id])

    def _login_and_get_response(self):
        """
        Logs the user in, attempts to access the contact-download view, and returns the response.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        return response

    def test_view_url_exists_for_logged_in_user_who_owns_contact(self):
        """
        Make sure that if the owner is logged in and attempts to access the contact-download view,
        they can do with success.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the contact-download view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")
    
    def test_404_if_logged_in_as_other_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-download view
        for a contact that does not belong to them, they are given a great big 404 right in their face. 
        """
        User.objects.create_user(username="tess_ting2", email="tess@ting2.com", password="password")
        self.client.login(username="tess_ting2", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_download_successful_if_logged_in_as_owner(self):
        """
        Make sure that if logged in as owner and Contact exists, image/png is returned.
        """
        response = self._login_and_get_response()
        self.assertEqual(response["Content-Type"], "text/vcard")
        self.assertEqual(response["Content-Disposition"], f"attachment; filename={slugify(self.contact.full_name)}.vcf")

    def test_404_if_contact_not_exists(self):
        """
        Make sure that if a Contact does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(reverse("contact-download", args=[self.contact.id + 1]))
        self.assertEqual(response.status_code, 404)


class TestContactListDownloadView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.url = reverse("contact-list-download")

    def _create_contact_for_user(self):
        """
        Creates a Contact for the user.
        """
        return Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )

    def _login_and_get_response(self):
        """
        Logs the user in, attempts to access the contact-list-download view, and returns the response.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        return response
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the contact-list-download view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")

    def test_view_url_exists_for_logged_in_user_with_contacts(self):
        """
        Make sure that if a logged in user with contacts attempts to access the contact-list-download
        view, they can do with success.
        """
        self._create_contact_for_user()
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)

    def test_successful_download_if_contacts_exist(self):
        """
        Make sure that if there are Contacts present, the response is a download.
        """
        self._create_contact_for_user()
        response = self._login_and_get_response()
        self.assertIn("Content-Disposition", response)
        self.assertEqual(response["Content-Disposition"], "attachment; filename=contacts.vcf")
        self.assertEqual(response["Content-Type"], "text/vcard")

    def test_status_404_if_no_contacts(self):
        """
        Make sure there is a 404 status code if there are no Contacts listed.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 404)

    def test_other_user_contacts_not_present_in_download(self):
        """
        Make sure that if there are Contacts present for other users,
        they are not included in the download.
        """
        other_user = User.objects.create_user(
            username="tess_ting2",
            email="tess@ting2.com",
            password="password"
        )
        Contact.objects.create(
            first_name="Nobody",
            middle_names="Likes",
            last_name="Me",
            user=other_user,
            year_met=2000
        )
        self._create_contact_for_user()
        response = self._login_and_get_response()
        self.assertIn("Content-Disposition", response)
        self.assertEqual(response["Content-Disposition"], "attachment; filename=contacts.vcf")
        self.assertEqual(response["Content-Type"], "text/vcard")
        vcard_data = response.content.decode("utf-8")
        self.assertIn("Wanted In Response", vcard_data)
        self.assertNotIn("Nobody Likes Me", vcard_data)


class TestContactListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.url = reverse("contact-list")

    def _create_contact_for_user(self):
        """
        Creates a Contact for the user.
        """
        return Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )

    def _login_and_get_response(self):
        """
        Logs the user in, attempts to access the contact-list view, and returns the response.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        return response
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the contact-list view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")

    def test_view_url_exists_for_logged_in_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-list view,
        they can do with success.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """
        Test that the view for a logged in user returns the contact_list.html template,
        and that the Download List button appears if Contacts are found for the list.
        """
        self._create_contact_for_user()
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/contact_list.html")
        self.assertContains(response, "Download List")

    def test_context_data(self):
        """
        Ensure that the context passed to the view contains the appropriate data.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)
        self.assertIn("filter_formset", response.context)

    def test_user_contact_present_in_context_data(self):
        """
        Make sure that the users contact is present in the contexts object_list.
        """
        contact = self._create_contact_for_user()
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)
        self.assertIn(contact, response.context["object_list"])

    def test_user_contact_appears_in_rendered_template(self):
        """
        Make sure that the users contact is rendered in the template.
        """
        contact = self._create_contact_for_user()
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)
        self.assertIn(contact, response.context["object_list"])
        self.assertTemplateUsed(response, "address_book/contact_list.html")
        self.assertContains(response, contact)

    def test_view_handles_no_contacts(self):
        """
        Make sure that an empty object_list is returned when no contacts are found,
        and that the 'Download List' button is hidden from the template.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["object_list"], [])
        self.assertNotContains(response, "Download List")

    def test_other_users_contacts_not_present_in_context_data(self):
        """
        Make sure that Contacts belonging to another User are not present in the contexts
        object_list.
        """
        other_user = User.objects.create_user(
            username="tess_ting2",
            email="tess@ting2.com",
            password="password"
        )
        Contact.objects.create(
            first_name="Unwanted",
            middle_names="In",
            last_name="Response",
            user=other_user,
            year_met=2000
        )
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)
        self.assertQuerySetEqual(response.context["object_list"], [])


class TestContactQrCodeView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        self.url = reverse("contact-qrcode", args=[self.contact.id])

    def _login_and_get_response(self):
        """
        Logs the user in, attempts to access the contact-qrcode view, and returns the response.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        return response

    def test_view_url_exists_for_logged_in_user_who_owns_contact(self):
        """
        Make sure that if the owner is logged in and attempts to access the contact-qrcode
        view, they can do with success.
        """
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
    
    def test_redirect_if_not_logged_in(self):
        """
        Make sure that if a non logged in user attempts to access the contact-qrcode view,
        they are redirected to the login page. 
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")
    
    def test_404_if_logged_in_as_other_user(self):
        """
        Make sure that if a logged in user attempts to access the contact-qrcode view
        for a contact that does not belong to them, they are given a great big 404 right in their face. 
        """
        User.objects.create_user(username="tess_ting2", email="tess@ting2.com", password="password")
        self.client.login(username="tess_ting2", password="password")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_png_returned_if_logged_in_as_owner(self):
        """
        Make sure that if logged in as owner and Contact exists, image/png is returned.
        """
        response = self._login_and_get_response()
        self.assertEqual(response["Content-Type"], "image/png")

    def test_404_if_contact_not_exists(self):
        """
        Make sure that if a Contact does not exist with the pk provided in the URL
        that the response status code is 404.
        """
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(reverse("contact-qrcode", args=[self.contact.id + 1]))
        self.assertEqual(response.status_code, 404)