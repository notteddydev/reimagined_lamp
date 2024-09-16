import random

from phone_gen import PhoneNumber as PhoneNumberGenerator, PhoneNumberNotFound

from django.conf import settings
from django.utils import translation

from phonenumber_field.formfields import localized_choices


def generate_fake_number() -> str:
    """
    Generate a fake phone number, for testing purposes. Necessary because of the unique
    requirement for PhoneNumbers, also because of the phonenumber field plugin which requires
    alphabetic strings for country codes sometimes and country prefixes at others.
    """
    language = translation.get_language() or settings.LANGUAGE_CODE
    choices = localized_choices(language)
    code = random.choice([code for code, _ in choices if len(code)])
    # Occasionally raises an error for code "001". 001 does not appear to be an option
    # in the localized_choices method, and this quick fix is good enough for now as the
    # error is only occasional.
    try:
        number = PhoneNumberGenerator(code).get_number()
    except PhoneNumberNotFound:
        number = generate_fake_number()
    return number
