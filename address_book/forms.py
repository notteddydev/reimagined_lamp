from django.forms import ModelForm

from .models import Address, Contact

class ContactForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(self, *args, **kwargs)
        self.fields['addresses'].queryset = Address.objects.filter(user=self.initial['user'])
        self.fields['family_members'].queryset = Contact.objects.filter(user=self.initial['user'])
        self.fields['met_through_contact'].queryset = Contact.objects.filter(user=self.initial['user'])

    # TODO
    # Find out why this is needed and if it should be different.
    def get(self, request):
        pass
        # super().get(self, request)

    class Meta:
        exclude = ['user']
        model = Contact