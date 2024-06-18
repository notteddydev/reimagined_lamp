from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, ListView

from .forms import ContactForm
from .models import Contact
from app.mixins import OwnedByUserMixin

class ContactListView(LoginRequiredMixin, OwnedByUserMixin, ListView):
    model = Contact
    
class ContactCreateView(LoginRequiredMixin, OwnedByUserMixin, CreateView):
    model = Contact
    form_class = ContactForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    

# TODO
# Can use OwnedByUserMixin here too. Leave as is for timebeing until there is an
# appropriate place to leave an example of UserPassesTestMixin too.
class ContactDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Contact

    def test_func(self) -> bool | None:
        return Contact.objects.filter(id=self.kwargs['pk'], user=self.request.user).exists()