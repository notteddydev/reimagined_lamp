from django.urls import path

from . import views

urlpatterns = [
    path("", views.ContactListView.as_view(), name="contact-list"),
    path("contacts/new", views.ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>", views.ContactDetailView.as_view(), name="contact-detail"),
]