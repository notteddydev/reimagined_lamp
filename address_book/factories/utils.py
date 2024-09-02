import random

from phone_gen import PhoneNumber as PhoneNumberGenerator

from django.conf import settings
from django.utils import translation

from phonenumber_field.formfields import localized_choices


def generate_fake_number() -> str:
    language = translation.get_language() or settings.LANGUAGE_CODE
    choices = localized_choices(language)
    code = random.choice([code for code, _ in choices if len(code)])
    number = PhoneNumberGenerator(code).get_number()
    return number