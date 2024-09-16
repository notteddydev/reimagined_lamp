from django import template

register = template.Library()


def filter_contact_list(filter_value: str, filter_field: str) -> str:
    """
    Turns a phone number or email address into a href of a determined type.
    """
    qs = "form-TOTAL_FORMS=1&"
    qs += "form-INITIAL_FORMS=0&"
    qs += "form-MIN_NUM_FORMS=0&"
    qs += "form-MAX_NUM_FORMS=1000&"
    qs += f"form-0-filter_field={filter_field}&"
    qs += f"form-0-filter_value={filter_value}&"

    return qs


register.filter("filter_contact_list", filter_contact_list)
