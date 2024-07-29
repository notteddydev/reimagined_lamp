from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from .models import Contact


class TestContactListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="tess_ting", email="tess@ting.com", password="password"
        )
        self.url = reverse("contact-list")

    def _login_and_get_response(self):
        self.client.login(username="tess_ting", password="password")
        response = self.client.get(self.url)
        return response
    
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{settings.LOGIN_URL}?next={self.url}")

    def test_view_url_exists_for_logged_in_user(self):
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address_book/contact_list.html")

    def test_context_data(self):
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)

    def test_user_contact_present_in_context_data(self):
        contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)
        self.assertIn(contact, response.context["object_list"])

    def test_user_contact_appears_in_rendered_template(self):
        contact = Contact.objects.create(
            first_name="Wanted",
            middle_names="In",
            last_name="Response",
            user=self.user,
            year_met=2000
        )
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertIn("object_list", response.context)
        self.assertIn(contact, response.context["object_list"])
        self.assertTemplateUsed(response, "address_book/contact_list.html")
        self.assertContains(response, contact)

    def test_view_handles_no_contacts(self):
        response = self._login_and_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["object_list"], [])

    def test_other_users_contacts_not_present_in_context_data(self):
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

