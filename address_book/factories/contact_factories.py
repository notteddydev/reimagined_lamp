import factory
import random

from datetime import datetime, timedelta
from django.db.models import QuerySet
from typing import List, Optional

from address_book import constants
from address_book.models import Contact, Nation, Profession, Tag, User
from .profession_factories import ProfessionFactory
from .user_factories import UserFactory


class ContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Contact

    first_name: str = factory.Faker("first_name")
    gender: str = factory.Iterator([constants.CONTACT_GENDER_FEMALE, constants.CONTACT_GENDER_MALE])
    is_business: bool = factory.LazyAttribute(
        lambda o: random.choice([True, False])
    )
    notes: str = factory.Faker("text", max_nb_chars=1000)
    last_name: str = factory.Faker("last_name")
    middle_names: str = factory.Faker("first_name")
    nickname: str = factory.Faker("first_name")
    website: str = factory.Faker("url")

    @factory.lazy_attribute
    def anniversary(self) -> datetime:
        delta_days: int = (self.dod - self.dob).days
        random_days: int = random.randint(0, delta_days)
        return self.dob + timedelta(days=random_days)

    @factory.lazy_attribute
    def dob(self) -> datetime:
        start_date: datetime = datetime(1900, 1, 1)
        end_date: datetime = datetime.now()
        delta_days: int = (end_date - start_date).days
        random_days: int = random.randint(0, delta_days)
        return start_date + timedelta(days=random_days)
    
    @factory.lazy_attribute
    def dod(self) -> datetime:
        end_date: datetime = datetime.now()
        delta_days: int = (end_date - self.dob).days
        random_days: int = random.randint(0, delta_days)
        return self.dob + timedelta(days=random_days)

    @factory.lazy_attribute
    def profession(self) -> Profession:
        existing_professions: QuerySet[Profession] = Profession.objects.all()

        if existing_professions.exists():
            return random.choice(existing_professions)
        else:
            return ProfessionFactory()

    @factory.lazy_attribute
    def user(self) -> User:
        existing_users: QuerySet[User] = User.objects.all()

        if existing_users.exists():
            return random.choice(existing_users)
        else:
            return UserFactory()
    
    @factory.lazy_attribute
    def year_met(self) -> int:
        delta_days: int = (self.dod - self.dob).days
        random_days: int = random.randint(0, delta_days)
        return (self.dob + timedelta(days=random_days)).year
    
    @factory.post_generation
    def family_members(self, create: bool, family_members: Optional[List[Contact]], **kwargs) -> None:
        if not create:
            return
        
        if family_members is not None:
            for family_member in family_members:
                self.family_members.add(family_member)

    @factory.post_generation
    def nationalities(self, create: bool, nationalities: Optional[List[Nation]], **kwargs) -> None:
        if not create:
            return
        
        if nationalities is None:
            nationalities: QuerySet[Nation] = Nation.objects.order_by("?")[:random.randint(1, 3)]

        for nationality in nationalities:
            self.nationalities.add(nationality)

    @factory.post_generation
    def tags(self, create: bool, tags: Optional[List[Tag]], **kwargs) -> None:
        if not create:
            return
        
        if tags is not None:
            for tag in tags:
                self.tags.add(tag)