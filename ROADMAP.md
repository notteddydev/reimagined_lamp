### ToDo (AddressBook)

forms.py
- validate that for forms with ModelMultipleChoice, and a User passed in form validation fails if Models that belong to another User are selected.
- Ensure that when a Tag is Updated (new TagUpdate view mentioned in views.py list), the disassociated contacts ARE disassociated. TESTS.
- Make it so that only existing models being updated in formsets have the option to be deleted.

models.py
- Maybe more effort that it's worth, but attach vcard to email / sms / whatsapp message
- validate that anniversary/dod is greater than dob
- validate that dod is greater than anniversary/dob
- change tag.name from unique; unique_together instead, for user and name.

views.py
- Create option to download a "lite" vcard, or customise what is downloaded.
- Deletion logic - contacts, addresses
- Allow importing of contacts from .vcf files.
- Make redirect from tag-create go to the contact that it was added from. From there they can click on the 'View Contacts' link to filter contacts by that tag.
- Make nationality links on contact-detail page link to contact-list filtering by nationality.
- Make sure that when creating an Address for a given Contact (passing contact-update contact.id to the address-create url as a next param), that the Address is pre-selected for a new Tenancy in the TenancyInlineFormSet.
- Add a TagUpdate view

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
- Remove typehints from variables. Only put them on method definitions.


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