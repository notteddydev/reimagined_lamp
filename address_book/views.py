from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, View
from django.urls import reverse

from .forms import ContactForm, PhoneNumberCreateFormSet, PhoneNumberUpdateFormSet
from .models import Contact, PhoneNumber
from app.mixins import OwnedByUserMixin

class ContactListView(LoginRequiredMixin, OwnedByUserMixin, ListView):
    model = Contact
    
class ContactCreateView(LoginRequiredMixin, OwnedByUserMixin, View):
    def get(self, request):
        return render(request, "address_book/contact_form.html", {
            "form": ContactForm(request.user),
            "phonenumber_formset": PhoneNumberCreateFormSet
        })
    
    def post(self, request):
        form = ContactForm(request.user, request.POST)
        phonenumber_formset = PhoneNumberCreateFormSet(request.POST)

        if form.is_valid() and phonenumber_formset.is_valid():
            contact = form.save()
            phone_numbers = phonenumber_formset.save(commit=False)

            for phone_number in phone_numbers:
                phone_number.contact = contact
                phone_number.save()

            return redirect("contact-list")

        return render(request, "address_book/contact_form.html", {
            "form": form,
            "phonenumber_formset": phonenumber_formset
        })
    

# TODO
# Can use OwnedByUserMixin here too. Leave as is for timebeing until there is an
# appropriate place to leave an example of UserPassesTestMixin too.
class ContactDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Contact

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['phone_numbers'] = PhoneNumber.objects.filter(contact=self.object)
        return context

    def test_func(self) -> bool | None:
        return Contact.objects.filter(id=self.kwargs['pk'], user=self.request.user).exists()
    

class ContactUpdateView(LoginRequiredMixin, OwnedByUserMixin, View):
    def get(self, request, pk):
        contact = Contact.objects.get(pk=pk)

        # TODO Look at changing the ContactForm so that in this case the user does not need passing in.
        return render(request, "address_book/contact_form.html", {
            "form": ContactForm(request.user, instance=contact),
            "object": contact,
            "phonenumber_formset": PhoneNumberUpdateFormSet(instance=contact)
        })
    
    def post(self, request, pk):
        contact = Contact.objects.get(pk=pk)
        form = ContactForm(request.user, request.POST, instance=contact)
        phonenumber_formset = PhoneNumberUpdateFormSet(request.POST, instance=contact)

        if form.is_valid() and phonenumber_formset.is_valid():
            contact = form.save()
            phone_numbers = phonenumber_formset.save(commit=False)

            for phone_number in phonenumber_formset.deleted_objects:
                phone_number.delete()

            for phone_number in phone_numbers:
                phone_number.contact = contact
                phone_number.save()

            return redirect(reverse("contact-detail", args=[contact.id]))

        return render(request, "address_book/contact_form.html", {
            "form": form,
            "phonenumber_formset": phonenumber_formset
        })