import factory
import random

from django.db.models import QuerySet
from typing import List, Optional

from address_book import constants
from address_book.models import Address, Contact, PhoneNumber, PhoneNumberType
from .address_factories import AddressFactory
from .contact_factories import ContactFactory
from .utils import generate_fake_number


class ContactPhoneNumberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PhoneNumber
        
    address_id = None
    archived = False
    number = factory.LazyFunction(generate_fake_number)

    @factory.lazy_attribute
    def contact(self) -> Contact:
        existing_contacts: QuerySet[Contact] = Contact.objects.all()

        if existing_contacts.exists():
            return random.choice(existing_contacts)
        else:
            return ContactFactory()
        
    @factory.post_generation
    def phonenumber_types(self, create: bool, phonenumber_types: Optional[List[PhoneNumberType]], **kwargs) -> None:
        if not create:
            return
        
        if phonenumber_types is None:
            phonenumber_types = PhoneNumberType.objects.exclude(
                name=constants.PHONENUMBERTYPE__NAME_PREF
            ).order_by("?")[:random.randint(1, 2)]
            
            contact_has_pref_phonenumber = self.contact.phonenumber_set.all().filter(
                phonenumber_types__name=constants.PHONENUMBERTYPE__NAME_PREF
            ).exists()

            if not contact_has_pref_phonenumber:
                pref_phonenumber_type = PhoneNumberType.objects.filter(name=constants.PHONENUMBERTYPE__NAME_PREF).first()
                self.phonenumber_types.add(pref_phonenumber_type)
        
        for phonenumber_type in phonenumber_types:
            self.phonenumber_types.add(phonenumber_type)


class AddressPhoneNumberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PhoneNumber
        
    archived = False
    contact_id = None
    number = factory.LazyFunction(generate_fake_number)

    @factory.lazy_attribute
    def address(self) -> Address:
        existing_addresss: QuerySet[Address] = Address.objects.all()

        if existing_addresss.exists():
            return random.choice(existing_addresss)
        else:
            return AddressFactory()
        
    @factory.post_generation
    def phonenumber_types(self, create: bool, phonenumber_types: Optional[List[PhoneNumberType]], **kwargs) -> None:
        if not create:
            return
        
        if phonenumber_types is None:
            phonenumber_types = PhoneNumberType.objects.exclude(
                name=constants.PHONENUMBERTYPE__NAME_PREF
            ).order_by("?")[:random.randint(1, 2)]
            
            address_has_pref_phonenumber = self.address.phonenumber_set.all().filter(
                phonenumber_types__name=constants.PHONENUMBERTYPE__NAME_PREF
            ).exists()

            if not address_has_pref_phonenumber:
                pref_phonenumber_type = PhoneNumberType.objects.filter(name=constants.PHONENUMBERTYPE__NAME_PREF).first()
                self.phonenumber_types.add(pref_phonenumber_type)
        
        for phonenumber_type in phonenumber_types:
            self.phonenumber_types.add(phonenumber_type)