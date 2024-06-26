from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, View

from .forms import ContactForm, PhoneNumberFormSet
from .models import Contact, PhoneNumber
from app.mixins import OwnedByUserMixin

class ContactListView(LoginRequiredMixin, OwnedByUserMixin, ListView):
    model = Contact
    
class ContactCreateView(LoginRequiredMixin, OwnedByUserMixin, View):
    def get(self, request):
        return render(request, "address_book/contact_form.html", {
            "form": ContactForm(**{"user": self.request.user}),
            "phonenumber_formset": PhoneNumberFormSet
        })
    
    def post(self, request):
        form = ContactForm(request.user, request.POST)
        phonenumber_formset = PhoneNumberFormSet(request.POST)

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