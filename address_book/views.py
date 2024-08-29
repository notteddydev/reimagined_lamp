from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.generic import DetailView, View

from .forms import AddressForm, AddressPhoneNumberCreateFormSet, AddressPhoneNumberUpdateFormSet, ContactFilterFormSet, ContactForm, ContactPhoneNumberCreateFormSet, ContactPhoneNumberUpdateFormSet, EmailFormSet, TagForm, TenancyCreateFormSet, TenancyUpdateFormSet, WalletAddressCreateFormSet, WalletAddressUpdateFormSet
from .models import Address, Contact
from app.decorators import owned_by_user
from app.mixins import OwnedByUserMixin

import qrcode
from io import BytesIO


@login_required
@owned_by_user(Contact)
def contact_download_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Downloads all non-archived vcardable Contact data as a .vcf file for a single Contact.
    """
    contact = get_object_or_404(Contact, pk=pk)

    response = HttpResponse(contact.vcard, content_type="text/vcard")
    response["Content-Disposition"] = f"attachment; filename={slugify(contact.full_name)}.vcf"

    return response


@login_required
def contact_list_download_view(request: HttpRequest) -> HttpResponse:
    """
    Downloads all non-archived vcardable Contact data as a .vcf file for a list of Contacts.
    """
    contacts = Contact.objects.filter(user=request.user)
    filter_formset = ContactFilterFormSet(request.GET or None)

    if filter_formset.is_valid():
        contacts = filter_formset.apply_filters(contacts)

    if not contacts.exists():
        raise Http404("No contacts were found for download.")

    vcards = [contact.vcard for contact in contacts]
    vcf = "\n".join(vcards)
    response = HttpResponse(vcf, content_type="text/vcard")
    response["Content-Disposition"] = "attachment; filename=contacts.vcf"
    return response


@login_required
def contact_list_view(request: HttpRequest) -> HttpResponse:
    """
    Lists Contacts for the logged in User; applying selected filters.
    """
    contacts = Contact.objects.filter(user=request.user)
    filter_formset = ContactFilterFormSet(request.GET or None)

    if filter_formset.is_valid():
        contacts = filter_formset.apply_filters(contacts)

    return render(request, "address_book/contact_list.html", {
        "object_list": contacts,
        "filter_formset": filter_formset,
    })


@login_required
@owned_by_user(Contact)
def contact_qrcode_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Returns a PNG image of a QR code which stores all non-archived vcardable Contact data
    for a given Contact.
    """
    contact = get_object_or_404(Contact, pk=pk)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(contact.vcard)
    qr.make(fit=True)

    # Create an image from the QR Code instance
    img = qr.make_image(fill="black", back_color="white")

    # Save it in a bytes buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer, content_type="image/png")
    

class AddressCreateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Return the address_form template for creating an Address.
        """
        return render(request, "address_book/address_form.html", {
            "form": AddressForm(request.user),
            "phonenumber_formset": AddressPhoneNumberCreateFormSet,
        })
    
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Creates an Address with valid data and redirects to the corresponding AddressDetail view;
        or, if incorrect data provided, returns the address_form template once again displaying
        errors.
        """
        form = AddressForm(request.user, request.POST)
        phonenumber_formset = AddressPhoneNumberCreateFormSet(request.POST)

        if form.is_valid() and phonenumber_formset.is_valid():
            address = form.save()
            phonenumber_formset.save_if_not_empty(instance=address)

            next_url = self.request.GET.get("next")
            if next_url:
                return redirect(next_url)

            return redirect(reverse("address-detail", args=[address.id]))

        return render(request, "address_book/address_form.html", {
            "form": form,
            "phonenumber_formset": phonenumber_formset,
        })
    

class AddressDetailView(LoginRequiredMixin, OwnedByUserMixin, DetailView):
    """
    Display details of a given Address.
    """
    model = Address
    

class AddressUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Return the address_form template for updating an Address, displaying any existing values.
        """
        address = get_object_or_404(Address, pk=pk)

        # TODO Look at changing the AddressForm so that in this case the user does not need passing in.
        return render(request, "address_book/address_form.html", {
            "form": AddressForm(request.user, instance=address),
            "object": address,
            "phonenumber_formset": AddressPhoneNumberUpdateFormSet(instance=address),
        })
    
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Updates an Address with valid data and redirects to the corresponding AddressDetail view;
        or, if incorrect data provided, returns the address_form template once again displaying
        errors.
        """
        address = get_object_or_404(Address, pk=pk)
        form = AddressForm(request.user, request.POST, instance=address)
        phonenumber_formset = AddressPhoneNumberUpdateFormSet(request.POST, instance=address)

        if form.is_valid() and phonenumber_formset.is_valid():
            address = form.save()
            phonenumber_formset.save_if_not_empty(instance=address)

            return redirect(reverse("address-detail", args=[address.id]))

        return render(request, "address_book/address_form.html", {
            "form": form,
            "object": address,
            "phonenumber_formset": phonenumber_formset,
        })

    def test_func(self) -> bool | None:
        return Address.objects.filter(id=self.kwargs["pk"], user=self.request.user).exists()


class ContactCreateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Return the contact_form template for creating an Contact.
        """
        return render(request, "address_book/contact_form.html", {
            "email_formset": EmailFormSet(),
            "form": ContactForm(request.user),
            "phonenumber_formset": ContactPhoneNumberCreateFormSet,
            "tenancy_formset": TenancyCreateFormSet(user=request.user),
            "walletaddress_formset": WalletAddressCreateFormSet,
        })
    
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Creates a Contact with valid data and redirects to the corresponding ContactDetail view;
        or, if incorrect data provided, returns the contact_form template once again displaying
        errors.
        """
        form = ContactForm(request.user, request.POST)
        
        formsets = {
            "email_formset": EmailFormSet(request.POST),
            "phonenumber_formset": ContactPhoneNumberCreateFormSet(request.POST),
            "tenancy_formset": TenancyCreateFormSet(request.POST, user=request.user),
            "walletaddress_formset": WalletAddressCreateFormSet(request.POST),
        }

        if form.is_valid() and all(formset.is_valid() for formset in formsets.values()):
            contact = form.save()
            for formset in formsets.values():
                formset.save_if_not_empty(instance=contact)

            return redirect(reverse("contact-detail", args=[contact.id]))

        return render(request, "address_book/contact_form.html", {
            **{"form": form},
            **{key: formset for key, formset in formsets.items()}
        })
    

class ContactDetailView(LoginRequiredMixin, OwnedByUserMixin, DetailView):
    """
    Display details of a given Contact .
    """
    model = Contact
    

class ContactUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Return the contact_form template for updating an Contact, displaying any existing values.
        """
        contact = get_object_or_404(Contact, pk=pk)

        # TODO Look at changing the ContactForm so that in this case the user does not need passing in.
        return render(request, "address_book/contact_form.html", {
            "email_formset": EmailFormSet(instance=contact),
            "form": ContactForm(request.user, instance=contact),
            "object": contact,
            "phonenumber_formset": ContactPhoneNumberUpdateFormSet(instance=contact),
            "tenancy_formset": TenancyUpdateFormSet(instance=contact, user=request.user),
            "walletaddress_formset": WalletAddressUpdateFormSet(instance=contact),
        })
    
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Updates an Contact with valid data and redirects to the corresponding ContactDetail view;
        or, if incorrect data provided, returns the contact_form template once again displaying
        errors.
        """
        contact = get_object_or_404(Contact, pk=pk)
        form = ContactForm(request.user, request.POST, instance=contact)

        formsets = {
            "email_formset": EmailFormSet(request.POST, instance=contact),
            "phonenumber_formset": ContactPhoneNumberUpdateFormSet(request.POST, instance=contact),
            "tenancy_formset": TenancyUpdateFormSet(request.POST, instance=contact, user=request.user),
            "walletaddress_formset": WalletAddressUpdateFormSet(request.POST, instance=contact),
        }

        if form.is_valid() and all(formset.is_valid() for formset in formsets.values()):
            contact = form.save()
            for formset in formsets.values():
                formset.save_if_not_empty(instance=contact)

            return redirect(reverse("contact-detail", args=[contact.id]))

        return render(request, "address_book/contact_form.html", {
            **{"form": form, "object": contact},
            **{key: formset for key, formset in formsets.items()}
        })

    def test_func(self) -> bool | None:
        return Contact.objects.filter(id=self.kwargs["pk"], user=self.request.user).exists()


class TagCreateView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Return the tag_form template for creating a Tag, pre-populating the associated
        contacts with any valid contact_id passed in the URL params.
        """
        contact_id = request.GET.get("contact_id")
        initial_data = {}
        
        if contact_id:
            user_owns_contact = Contact.objects.filter(id=contact_id, user=request.user).exists()

            if user_owns_contact:
                initial_data = {"contacts": (int(contact_id),)}

        form = TagForm(request.user, initial=initial_data)

        return render(request, "address_book/tag_form.html", {
            "form": form,
        })
    
    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Creates an Tag with valid data and redirects to the ContactList view, filtering by
        the created Tag; or, if incorrect data provided, returns the tag_form template once
        again displaying errors.
        """
        form = TagForm(request.user, request.POST)

        if form.is_valid():
            form.save()

            return redirect("contact-list")

        return render(request, "address_book/tag_form.html", {
            "form": form,
        })