### ToDo (AddressBook)

forms.py
- Make it so that only existing models being updated in formsets have the option to be deleted.

models.py
- Maybe more effort that it's worth, but attach vcard to email / sms / whatsapp message
- Timestamping / soft deleting

views.py
- Create option to download a "lite" vcard, or customise what is downloaded.
- Allow importing of contacts from .vcf files.

templates
- Add JavaScript for adding / removing forms from formsets for tidier forms.

utils.py
- vcard object for setting / getting properties of a vcard? Useful for import / export

other

general
- Add a site-wide button which hides archived items from all views.


### Long-term

- Calendar (hourly)
- Notes
- Lists
- Journaling
- Finance tracking
- Locations list
  - Emergency numbers
  - Plug type
  - Interactive map
- Weather forecast