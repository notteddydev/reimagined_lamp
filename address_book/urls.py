from django.urls import path
import importlib

def get_my_model_view(my_model_view: str):
    # Dynamically import the view module
    views_module = importlib.import_module('address_book.views')
    return getattr(views_module, my_model_view)

urlpatterns = [
    path("contacts/new", get_my_model_view("ContactCreateView").as_view(), name="contact-create"),
    path("contacts/<int:pk>/delete", get_my_model_view("ContactDeleteView").as_view(), name="contact-delete"),
    path("contacts/<int:pk>", get_my_model_view("ContactDetailView").as_view(), name="contact-detail"),
    path("contacts/", get_my_model_view("contact_list_view"), name="contact-list"),
    path("contacts/download", get_my_model_view("contact_list_download_view"), name="contact-list-download"),
    path("contacts/<int:pk>/edit", get_my_model_view("ContactUpdateView").as_view(), name="contact-update"),
    path("contacts/<int:pk>/qrcode", get_my_model_view("contact_qrcode_view"), name="contact-qrcode"),
    path("contacts/<int:pk>/download", get_my_model_view("contact_download_view"), name="contact-download"),
    path("tags/new", get_my_model_view("TagCreateView").as_view(), name="tag-create"),
    path("tags/<int:pk>/edit", get_my_model_view("TagUpdateView").as_view(), name="tag-update"),
    path("tags/<int:pk>/delete", get_my_model_view("TagDeleteView").as_view(), name="tag-delete"),
    path("tenancies/<int:pk>/delete", get_my_model_view("TenancyDeleteView").as_view(), name="tenancy-delete"),
    path("addresses/<int:pk>/edit", get_my_model_view("AddressUpdateView").as_view(), name="address-update"),
    path("addresses/new", get_my_model_view("AddressCreateView").as_view(), name="address-create"),
    path("addresses/<int:pk>/delete", get_my_model_view("AddressDeleteView").as_view(), name="address-delete"),
    path("addresses/<int:pk>", get_my_model_view("AddressDetailView").as_view(), name="address-detail"),
]