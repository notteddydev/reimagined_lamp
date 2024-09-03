import random

from phone_gen import PhoneNumber as PhoneNumberGenerator, PhoneNumberNotFound

from django.conf import settings
from django.utils import translation

from phonenumber_field.formfields import localized_choices


def generate_fake_number() -> str:
    language = translation.get_language() or settings.LANGUAGE_CODE
    choices = localized_choices(language)
    code = random.choice([code for code, _ in choices if len(code)])
    # Occasionally raises an error for code "001". 001 does not appear to be an option
    # in the localized_choices method, and this quick fix is good enough for now as the
    # error is only occasional.
    try:
        number = PhoneNumberGenerator(code).get_number()
    except PhoneNumberNotFound:
        generate_fake_number()
    return number