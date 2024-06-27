from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View
from django.urls import reverse

from .forms import ContactForm, EmailCreateFormSet, EmailUpdateFormSet, PhoneNumberCreateFormSet, PhoneNumberUpdateFormSet, TagForm
from .models import Contact, Email, PhoneNumber, Tag
from app.mixins import OwnedByUserMixin

class ContactListView(LoginRequiredMixin, OwnedByUserMixin, ListView):
    model = Contact
    
class ContactCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "address_book/contact_form.html", {
            "email_formset": EmailCreateFormSet,
            "form": ContactForm(request.user),
            "phonenumber_formset": PhoneNumberCreateFormSet,
        })
    
    def post(self, request):
        form = ContactForm(request.user, request.POST)
        email_formset = EmailCreateFormSet(request.POST)
        phonenumber_formset = PhoneNumberCreateFormSet(request.POST)

        if form.is_valid() and email_formset.is_valid() and phonenumber_formset.is_valid():
            contact = form.save()

            email_formset.instance = contact
            email_formset.save()

            phonenumber_formset.instance = contact
            phonenumber_formset.save()

            return redirect("contact-list")

        return render(request, "address_book/contact_form.html", {
            "email_formset": email_formset,
            "form": form,
            "phonenumber_formset": phonenumber_formset,
        })
    

class ContactDetailView(LoginRequiredMixin, OwnedByUserMixin, DetailView):
    model = Contact

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['emails'] = Email.objects.filter(contact=self.object)
        context['phone_numbers'] = PhoneNumber.objects.filter(contact=self.object)
        context['tags'] = Tag.objects.filter(contact=self.object)
        return context
    

class ContactUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)

        # TODO Look at changing the ContactForm so that in this case the user does not need passing in.
        return render(request, "address_book/contact_form.html", {
            "email_formset": EmailUpdateFormSet(instance=contact),
            "form": ContactForm(request.user, instance=contact),
            "object": contact,
            "phonenumber_formset": PhoneNumberUpdateFormSet(instance=contact)
        })
    
    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        form = ContactForm(request.user, request.POST, instance=contact)
        email_formset = EmailUpdateFormSet(request.POST, instance=contact)
        phonenumber_formset = PhoneNumberUpdateFormSet(request.POST, instance=contact)

        if form.is_valid() and email_formset.is_valid() and phonenumber_formset.is_valid():
            contact = form.save()

            email_formset.instance = contact
            email_formset.save()

            phonenumber_formset.instance = contact
            phonenumber_formset.save()

            return redirect(reverse("contact-detail", args=[contact.id]))

        return render(request, "address_book/contact_form.html", {
            "email_formset": email_formset,
            "form": form,
            "object": contact,
            "phonenumber_formset": phonenumber_formset,
        })

    def test_func(self) -> bool | None:
        return Contact.objects.filter(id=self.kwargs['pk'], user=self.request.user).exists()


# TODO bin this in favour of a filtered ContactListView
class TagListView(LoginRequiredMixin, OwnedByUserMixin, ListView):
    model = Tag


class TagCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "address_book/tag_form.html", {
            "form": TagForm(request.user),
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
    

class TagDetailView(LoginRequiredMixin, OwnedByUserMixin, DetailView):
    model = Tag

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['contacts'] = Contact.objects.filter(tags=self.object)
        return context