from django.urls import path

from . import views

urlpatterns = [
    path("contacts/new", views.ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>", views.ContactDetailView.as_view(), name="contact-detail"),
    path("contacts/", views.ContactListView.as_view(), name="contact-list"),
    path("contacts/<int:pk>/edit", views.ContactUpdateView.as_view(), name="contact-update"),
    path("tags/new", views.TagCreateView.as_view(), name="tag-create"),
    path("tags/<int:pk>", views.TagDetailView.as_view(), name="tag-detail"),
    path("addresses/<int:pk>/edit", views.AddressUpdateView.as_view(), name="address-update"),
    path("addresses/new", views.AddressCreateView.as_view(), name="address-create"),
    path("addresses/<int:pk>", views.AddressDetailView.as_view(), name="address-detail"),
]