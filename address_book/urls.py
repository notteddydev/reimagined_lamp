from django.urls import path

from .views import AddressCreateView, AddressDeleteView, AddressDetailView, AddressUpdateView, ContactCreateView, ContactDeleteView, ContactDetailView, contact_download_view, contact_list_download_view, contact_list_view, contact_qrcode_view, ContactUpdateView, TagCreateView, TagDeleteView, TagUpdateView, TenancyDeleteView

urlpatterns = [
    path("addresses/new", AddressCreateView.as_view(), name="address-create"),
    path("addresses/<int:pk>/delete", AddressDeleteView.as_view(), name="address-delete"),
    path("addresses/<int:pk>", AddressDetailView.as_view(), name="address-detail"),
    path("addresses/<int:pk>/edit", AddressUpdateView.as_view(), name="address-update"),
    path("contacts/new", ContactCreateView.as_view(), name="contact-create"),
    path("contacts/<int:pk>/delete", ContactDeleteView.as_view(), name="contact-delete"),
    path("contacts/<int:pk>", ContactDetailView.as_view(), name="contact-detail"),
    path("contacts/<int:pk>/download", contact_download_view, name="contact-download"),
    path("contacts/download", contact_list_download_view, name="contact-list-download"),
    path("contacts/", contact_list_view, name="contact-list"),
    path("contacts/<int:pk>/qrcode", contact_qrcode_view, name="contact-qrcode"),
    path("contacts/<int:pk>/edit", ContactUpdateView.as_view(), name="contact-update"),
    path("tags/new", TagCreateView.as_view(), name="tag-create"),
    path("tags/<int:pk>/delete", TagDeleteView.as_view(), name="tag-delete"),
    path("tags/<int:pk>/edit", TagUpdateView.as_view(), name="tag-update"),
    path("tenancies/<int:pk>/delete", TenancyDeleteView.as_view(), name="tenancy-delete"),
]