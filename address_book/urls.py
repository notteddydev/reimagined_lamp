from django.urls import path

from . import views

urlpatterns = [
    path("contacts/new", views.ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>", views.ContactDetailView.as_view(), name="contact-detail"),
    path("contacts/", views.ContactListView.as_view(), name="contact-list"),
    path("contacts/download", views.contact_list_download_view, name="contacts-download"),
    path("contacts/<int:pk>/edit", views.ContactUpdateView.as_view(), name="contact-update"),
    path("contacts/<int:pk>/qrcode", views.contact_qrcode, name="contact-qrcode"),
    path("contacts/<int:pk>/download", views.contact_download, name="contact-download"),
    path("tags/new", views.TagCreateView.as_view(), name="tag-create"),
    path("addresses/<int:pk>/edit", views.AddressUpdateView.as_view(), name="address-update"),
    path("addresses/new", views.AddressCreateView.as_view(), name="address-create"),
    path("addresses/<int:pk>", views.AddressDetailView.as_view(), name="address-detail"),
]