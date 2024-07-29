from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Contact


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

    def _login_and_get_response(self, url=None):
        """
        Logs the user in, attempts to access the contact-list view, and returns the response.
        """
        get_url = self.url if url == None else url
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(get_url)
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
        other_user = User.objects.create(
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

    def test_normal_view_returned_if_download_false(self):
        """
        Make sure that if the download param is passed to the request as false,
        the normal view and associated template are returned.
        """
        response = self._login_and_get_response(f"{self.url}?download=false")
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        self.assertTemplateUsed(response, "address_book/contact_list.html")

    def test_successful_download_if_true_and_contacts_exist(self):
        """
        Make sure that if the download param is passed to the request as true,
        and there are Contacts present, the response is a download.
        """
        self._create_contact_for_user()
        response = self._login_and_get_response(f"{self.url}?download=true")
        self.assertIn("Content-Disposition", response)
        self.assertEqual(response["Content-Disposition"], "attachment; filename=contacts.vcf")
        self.assertEqual(response["Content-Type"], "text/vcard")

    def test_status_404_if_download_forced_for_no_contacts(self):
        """
        Make sure there is a 404 status code if someone types download=true into the
        address bar even though there are no Contacts listed.
        """
        response = self._login_and_get_response(f"{self.url}?download=true")
        self.assertEqual(response.status_code, 404)
