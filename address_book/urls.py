from django.urls import path

from . import views

urlpatterns = [
    path("contacts/new", views.ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>", views.ContactDetailView.as_view(), name="contact-detail"),
    path("contacts/", views.ContactListView.as_view(), name="contact-list"),
    path("contacts/<int:pk>/edit", views.ContactUpdateView.as_view(), name="contact-update")
]