import factory
from django.contrib.auth.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username: str = factory.Faker("user_name")
    email: str = factory.Faker("email")
    password: str = factory.PostGenerationMethodCall("set_password", "password123")
