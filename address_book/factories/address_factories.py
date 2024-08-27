import factory
import random

from django.db.models import QuerySet

from address_book.models import Address, Nation, User
from .user_factories import UserFactory


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    address_line_1: str = factory.Faker("street_address")
    address_line_2: str = factory.Faker("secondary_address")
    city: str = factory.Faker("city")
    neighbourhood: str = factory.Faker("street_name")
    notes: str = factory.Faker("text", max_nb_chars=1000)
    postcode: str = factory.Faker("postcode")
    state: str = factory.Faker("state")

    @factory.lazy_attribute
    def country(self) -> Nation:
        existing_countries: QuerySet[Nation] = Nation.objects.all()

        return random.choice(existing_countries)

    @factory.lazy_attribute
    def user(self) -> User:
        existing_users: QuerySet[User] = User.objects.all()

        if existing_users.exists():
            return random.choice(existing_users)
        else:
            return UserFactory()