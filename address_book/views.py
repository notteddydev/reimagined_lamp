from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.generic import DetailView, ListView, View

from .forms import AddressForm, AddressPhoneNumberCreateFormSet, AddressPhoneNumberUpdateFormSet, ContactFilterFormSet, ContactForm, ContactPhoneNumberCreateFormSet, ContactPhoneNumberUpdateFormSet, EmailCreateFormSet, EmailUpdateFormSet, TagForm, WalletAddressCreateFormSet, WalletAddressUpdateFormSet
from .models import Address, Contact, ContactAddress
from app.decorators import owned_by_user
from app.mixins import OwnedByUserMixin

import qrcode
from io import BytesIO


@login_required
@owned_by_user(Contact)
def contact_download_view(request, pk):
    contact = get_object_or_404(Contact, pk=pk)

    response = HttpResponse(contact.vcard, content_type="text/vcard")
    response["Content-Disposition"] = f"attachment; filename={slugify(contact.full_name)}.vcf"

    return response


@login_required
def contact_list_download_view(request):
    contacts = Contact.objects.filter(user=request.user)
    filter_formset = ContactFilterFormSet(request.GET or None)

    if filter_formset.is_valid():
        contacts = filter_formset.apply_filters(contacts)

    if not contacts.exists():
        raise Http404("No contacts were found for download.")

    vcards = [contact.vcard for contact in contacts]
    vcf = "\n".join(vcards)
    response = HttpResponse(vcf, content_type="text/vcard")
    response['Content-Disposition'] = "attachment; filename=contacts.vcf"
    return response


@login_required
def contact_list_view(request):
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
def contact_qrcode_view(request, pk):
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
    def get(self, request):
        contact_id = request.GET.get("contact_id")
        initial_data = {}

        if contact_id:
            user_owns_contact = Contact.objects.filter(user=request.user, pk=contact_id).exists()

            if user_owns_contact:
                initial_data = {"contacts": (int(contact_id),)}

        form = AddressForm(request.user, initial=initial_data)

        return render(request, "address_book/address_form.html", {
            "form": form,
            "phonenumber_formset": AddressPhoneNumberCreateFormSet,
        })
    
    def post(self, request):
        form = AddressForm(request.user, request.POST)
        phonenumber_formset = AddressPhoneNumberCreateFormSet(request.POST)

        if form.is_valid() and phonenumber_formset.is_valid():
            address = form.save()

            phonenumber_formset.instance = address
            phonenumber_formset.save()

            return redirect(reverse("address-detail", args=[address.id]))

        return render(request, "address_book/address_form.html", {
            "form": form,
            "phonenumber_formset": phonenumber_formset,
        })
    

class AddressDetailView(LoginRequiredMixin, OwnedByUserMixin, DetailView):
    model = Address
    

class AddressUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        address = get_object_or_404(Address, pk=pk)

        # TODO Look at changing the AddressForm so that in this case the user does not need passing in.
        return render(request, "address_book/address_form.html", {
            "form": AddressForm(request.user, instance=address),
            "object": address,
            "phonenumber_formset": AddressPhoneNumberUpdateFormSet(instance=address),
        })
    
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk)
        form = AddressForm(request.user, request.POST, instance=address)
        phonenumber_formset = AddressPhoneNumberUpdateFormSet(request.POST, instance=address)

        if form.is_valid() and phonenumber_formset.is_valid():
            address = form.save()

            phonenumber_formset.instance = address
            phonenumber_formset.save()

            return redirect(reverse("address-detail", args=[address.id]))

        return render(request, "address_book/address_form.html", {
            "form": form,
            "object": address,
            "phonenumber_formset": phonenumber_formset,
        })

    def test_func(self) -> bool | None:
        return Address.objects.filter(id=self.kwargs['pk'], user=self.request.user).exists()


class ContactAddressToggleArchiveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def post(self, request, pk):
        contactaddress = get_object_or_404(ContactAddress, pk=pk)
        contactaddress.archived = not contactaddress.archived
        contactaddress.save()

        return HttpResponseRedirect(request.META["HTTP_REFERER"])

    def test_func(self) -> bool | None:
        return ContactAddress.objects.filter(pk=self.kwargs['pk'], contact__user=self.request.user).exists()


class ContactCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "address_book/contact_form.html", {
            "email_formset": EmailCreateFormSet,
            "form": ContactForm(request.user),
            "phonenumber_formset": ContactPhoneNumberCreateFormSet,
            "walletaddress_formset": WalletAddressCreateFormSet,
        })
    
    def post(self, request):
        form = ContactForm(request.user, request.POST)
        email_formset = EmailCreateFormSet(request.POST)
        phonenumber_formset = ContactPhoneNumberCreateFormSet(request.POST)
        walletaddress_formset = WalletAddressCreateFormSet(request.POST)

        if form.is_valid() and email_formset.is_valid() and phonenumber_formset.is_valid() and walletaddress_formset.is_valid():
            contact = form.save()

            email_formset.instance = contact
            email_formset.save()

            phonenumber_formset.instance = contact
            phonenumber_formset.save()

            walletaddress_formset.instance = contact
            walletaddress_formset.save()

            return redirect(reverse("contact-detail", args=[contact.id]))

        return render(request, "address_book/contact_form.html", {
            "email_formset": email_formset,
            "form": form,
            "phonenumber_formset": phonenumber_formset,
            "walletaddress_formset": walletaddress_formset,
        })
    

class ContactDetailView(LoginRequiredMixin, OwnedByUserMixin, DetailView):
    model = Contact
    

class ContactUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)

        # TODO Look at changing the ContactForm so that in this case the user does not need passing in.
        return render(request, "address_book/contact_form.html", {
            "email_formset": EmailUpdateFormSet(instance=contact),
            "form": ContactForm(request.user, instance=contact),
            "object": contact,
            "phonenumber_formset": ContactPhoneNumberUpdateFormSet(instance=contact),
            "walletaddress_formset": WalletAddressUpdateFormSet(instance=contact),
        })
    
    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        form = ContactForm(request.user, request.POST, instance=contact)
        email_formset = EmailUpdateFormSet(request.POST, instance=contact)
        phonenumber_formset = ContactPhoneNumberUpdateFormSet(request.POST, instance=contact)
        walletaddress_formset = WalletAddressUpdateFormSet(request.POST, instance=contact)

        if form.is_valid() and email_formset.is_valid() and phonenumber_formset.is_valid() and walletaddress_formset.is_valid():
            contact = form.save()

            email_formset.instance = contact
            email_formset.save()

            phonenumber_formset.instance = contact
            phonenumber_formset.save()

            walletaddress_formset.instance = contact
            walletaddress_formset.save()

            return redirect(reverse("contact-detail", args=[contact.id]))

        return render(request, "address_book/contact_form.html", {
            "email_formset": email_formset,
            "form": form,
            "object": contact,
            "phonenumber_formset": phonenumber_formset,
            "walletaddress_formset": walletaddress_formset,
        })

    def test_func(self) -> bool | None:
        return Contact.objects.filter(id=self.kwargs['pk'], user=self.request.user).exists()


class TagCreateView(LoginRequiredMixin, View):
    def get(self, request):
        if request.GET.get("contact_id"):
            form = TagForm(request.user, initial={"contacts": (request.GET.get("contact_id"))})
        else:
            form = TagForm(request.user)

        return render(request, "address_book/tag_form.html", {
            "form": form,
        })
    
    def post(self, request):
        form = TagForm(request.user, request.POST)

        if form.is_valid():
            tag = form.save()
            
            contacts_selected = form.cleaned_data['contacts']
            for contact in contacts_selected:
                contact.tags.add(tag)

            return redirect("tag-list")

        return render(request, "address_book/tag_form.html", {
            "form": form,
        })