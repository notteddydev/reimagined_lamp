import factory
import random

from django.db.models import QuerySet
from typing import List, Optional

from address_book import constants
from address_book.models import Contact, Email, EmailType
from .contact_factories import ContactFactory


class EmailFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Email
        
    archived = False
    email = factory.Faker("email")

    @factory.lazy_attribute
    def contact(self) -> Contact:
        existing_contacts: QuerySet[Contact] = Contact.objects.all()

        if existing_contacts.exists():
            return random.choice(existing_contacts)
        else:
            return ContactFactory()
        
    @factory.post_generation
    def email_types(self, create: bool, email_types: Optional[List[EmailType]], **kwargs) -> None:
        if not create:
            return
        
        if email_types is None:
            email_types = EmailType.objects.exclude(
                name=constants.EMAILTYPE__NAME_PREF
            ).order_by("?")[:random.randint(1, 2)]
            
            contact_has_pref_email = self.contact.email_set.all().filter(
                email_types__name=constants.EMAILTYPE__NAME_PREF
            ).exists()

            if not contact_has_pref_email:
                pref_email_type = EmailType.objects.filter(name=constants.EMAILTYPE__NAME_PREF).first()
                self.email_types.add(pref_email_type)
        
        for email_type in email_types:
            self.email_types.add(email_type)