from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, DetailView, ListView

from .models import Contact
from app.mixins import OwnedByUserMixin

class ContactListView(LoginRequiredMixin, OwnedByUserMixin, ListView):
    model = Contact
    
class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    fields = '__all__'

# TODO
# Can use OwnedByUserMixin here too. Leave as is for timebeing until there is an
# appropriate place to leave an example of UserPassesTestMixin too.
class ContactDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Contact

    def test_func(self) -> bool | None:
        return Contact.objects.filter(id=self.kwargs['pk'], user=self.request.user).exists()