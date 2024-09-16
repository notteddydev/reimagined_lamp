from django import template

register = template.Library()


def hreffer(value: str, href_type: str) -> str:
    """
    Turns a phone number or email address into a href of a determined type.
    """
    HREFS = {
        "email": lambda email: f"malto:{email}",
        "tel": lambda tel: f"tel:{tel}",
        "sms": lambda sms: f"sms:{sms}",
        "whatsapp": lambda whatsapp: f"https://wa.me/{whatsapp}",
    }

    if href_type not in HREFS:
        raise KeyError(f"'{href_type}' key does not exist in dictionary.")

    return HREFS[href_type](value)


register.filter("hreffer", hreffer)
