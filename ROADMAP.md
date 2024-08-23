### ToDo (AddressBook)

forms.py
- Check form validation; validate that an address is always associated with at least one contact.
- Consolidate VERY NOT DRY code in Email and Phone Forms and Formsets. And Address. cleaning types.
- Find out how to not have to create 'CreateFormSet' and 'UpdateFormSet' just to set the can_delete value differently.
- Make InlineFormSets work consistently whereby they do not throw just one error if there are many; the array of errors is thrown as in the TenancyFormSet

models.py
- Maybe more effort that it's worth, but attach vcard to email / sms / whatsapp message

views.py
- Create option to download a "lite" vcard, or customise what is downloaded.
- Deletion logic - contacts, addresses
- Allow importing of contacts from .vcf files.
- Make redirect from tag-create automatically filter contact-list by tag name again
- Make sure that when creating an Address for a given Contact (passing contact-update contact.id to the address-create url as a next param), that the Address is pre-selected for a new Tenancy in the TenancyInlineFormSet.

tests.py
- Test everything.

templates
- Add JavaScript for adding / removing forms from formsets for tidier forms.

utils.py
- vcard object for setting / getting properties of a vcard? Useful for import / export

other
- Setup GitHub pipeline.
- Set up with nginx on local

general
- Erm... add docblocks, pattern code, add typehints, refactor code - view classes particularly.
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