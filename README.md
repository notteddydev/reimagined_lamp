# reimagined_lamp
Python and Django personal organiser (currently just address book).

### ToDo (AddressBook)

- Bin AddressDetail view, in favour of a TenancyDetail view.
- TenancyDetail view shows all the same stuff as the AddressDetail view as well as the TENANCY-SPECIFIC AddressType, and it's archived state for that Tenancy.
- Add TenancyInlineFormSet to AddressForm
- Bin ToggleTenancyArchived view in favour of TenancyUpdate view.

- Ermm... maybe... like... add some tests
- Erm... add docblocks, pattern code, add typehints, refactor code - view classes particularly.
- Check form validation; validate that an address is always associated with at least one contact.
- Change look of login page if logged in / redirect.
- Setup GitHub pipeline.
- Swap single quotes for double quotes throughout project.
- Add JavaScript for adding / removing forms from formsets for tidier forms.
- Consolidate VERY NOT DRY code in Email and Phone Forms and Formsets. And Address. cleaning types.
- Create option to download a "lite" vcard, or customise what is downloaded.
- Deletion logic - contacts, addresses
- Look into related descriptors and using a custom ManyToManyDescriptor for Addresses to Contacts to make sure that Address always comes prepopulated with the 'archived' db field. As well as a custom object manager.
- Add is_empty property to Formsets? (see AddressCreateView post)
- Maybe more effort that it's worth, but attach vcard to email / sms / whatsapp message
- Add a site-wide button which hides archived items from all views.
- Allow importing of contacts from .vcf files.
- Determine how to deal with Address / AddressType issue. i.e. an Address can have AddressType of 'PREF'... but that doesn't specify which Contact the Address is the preferred for. Maybe AddressType should be related to ContactAddress instead? Not a big deal though. Sort it later.
- Find out why profession seems to get overridden by email address when scanning qr code on iphone.
- vcard object for setting / getting properties of a vcard? Useful for import / export
- Set up with nginx on local
- Prevent 'profession' from being a required field.
- Create method on ContactableType / QuerySet / something to find the 'preferred' type. REPLACE the horrible methods in test_views.py


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


### Handy Links

- [vCard docs](https://en.wikipedia.org/wiki/VCard)
- [Django naming conventions](https://stackoverflow.com/questions/31816624/naming-convention-for-django-url-templates-models-and-views)
- [Setting up a django project with pipenv](https://python.plainenglish.io/setting-up-a-basic-django-project-with-pipenv-7c58fa2ec631)
- [Creating a vcard qrcode in python](https://www.joshfinnie.com/blog/creating-a-vcard-qr-code-in-python/)
- [Countries with regional codes](https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes/blob/master/all/all.csv)