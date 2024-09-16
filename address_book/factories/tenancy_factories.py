import factory
import random

from address_book import constants
from address_book.factories.address_factories import AddressFactory
from address_book.factories.contact_factories import ContactFactory
from address_book.models import Address, AddressType, Contact, Tenancy

from typing import Optional, List


class TenancyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenancy

    archived = False

    @factory.lazy_attribute
    def address(self) -> Address:
        existing_addresses = Address.objects.all()

        if existing_addresses.exclude(tenancy__contact=self.contact).exists():
            return random.choice(existing_addresses)
        else:
            return AddressFactory()

    @factory.lazy_attribute
    def contact(self) -> Contact:
        existing_contacts = Contact.objects.all()

        if existing_contacts.exclude(tenancy__address=self.address).exists():
            return random.choice(existing_contacts)
        else:
            return ContactFactory()

    @factory.post_generation
    def tenancy_types(self, create: bool, tenancy_types: Optional[List[AddressType]], **kwargs) -> None:
        if not create:
            return

        if tenancy_types is None:
            tenancy_types = AddressType.objects.exclude(
                name=constants.ADDRESSTYPE__NAME_PREF
            ).order_by("?")[:random.randint(1, 2)]

            contact_has_pref_tenancy = self.contact.tenancy_set.all().filter(
                tenancy_types__name=constants.ADDRESSTYPE__NAME_PREF
            ).exists()

            if not contact_has_pref_tenancy:
                pref_tenancy_type = AddressType.objects.filter(name=constants.ADDRESSTYPE__NAME_PREF).first()
                self.tenancy_types.add(pref_tenancy_type)

        for tenancy_type in tenancy_types:
            self.tenancy_types.add(tenancy_type)
