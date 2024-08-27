import factory

from address_book.models import Profession


class ProfessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profession

    name: str = factory.Faker("word")