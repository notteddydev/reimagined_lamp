from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Contact


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
        Make sure that if a logged in user attempts to access the contact-list-download view,
        they can do with success.
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
    
    def test_redirect_if_logged_in_as_other_user(self):
        """
        Make sure that if a non logged in user attempts to access the contact-list-download view,
        they are redirected to the login page. 
        """
        User.objects.create_user(username="tess_ting2", email="tess@ting2.com", password="password")
        self.client.login(username="tess_ting2", password="password")
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")