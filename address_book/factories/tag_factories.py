import factory
import random

from django.db.models import QuerySet

from address_book.models import Tag, User
from .user_factories import UserFactory


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("word")

    @factory.lazy_attribute
    def user(self) -> User:
        existing_users: QuerySet[User] = User.objects.all()

        if existing_users.exists():
            return random.choice(existing_users)
        else:
            return UserFactory()