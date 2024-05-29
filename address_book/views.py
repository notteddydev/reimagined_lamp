from django.shortcuts import render
from django.views.generic import CreateView, ListView

from .models import Contact

class ContactListView(ListView):
    model = Contact


class ContactCreateView(CreateView):
    model = Contact
    fields = '__all__'