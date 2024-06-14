from django.forms import ModelForm

from .models import Contact, Tag

class ContactForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(self, *args, **kwargs)
        self.fields['family_members'].queryset = Contact.objects.filter(user=self.initial['user'])
        self.fields['tags'].queryset = Tag.objects.filter(user=self.initial['user'])

    # TODO
    # Find out why this is needed and if it should be different.
    def get(self, request):
        pass
        # super().get(self, request)

    class Meta:
        exclude = ['addresses', 'user']
        model = Contact