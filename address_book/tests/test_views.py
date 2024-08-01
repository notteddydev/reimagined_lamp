from collections import Counter
from django.conf import settings
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.test import Client, TestCase
from django.urls import reverse

from address_book.models import Address, Contact


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
            "phonenumber_set-0-phonenumber_types": ["1", "10"],
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
            "phonenumber_set-0-phonenumber_types": ["1", "10"],
            "phonenumber_set-0-id": [""],
            "phonenumber_set-0-address": [""],
            "phonenumber_set-1-number_0": ["GB"],
            "phonenumber_set-1-number_1": [""],
            "phonenumber_set-1-id": [""],
            "phonenumber_set-1-address": [""]
        }
        response = self.client.post(self.url, invalid_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(reverse("address-create"))
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