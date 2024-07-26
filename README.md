### ToDo (AddressBook)

- Add option to filter by multiple fields to ContactList
- Ermm... maybe... like... add some tests
- Erm... add docblocks, pattern code, add typehints, refactor code - view classes particularly.
- Check form validation
- Consolidate VERY NOT DRY code in Email and Phone Forms and Formsets.
- Create option to download a "lite" vcard, or customise what is downloaded.
- Deletion logic - contacts, addresses
- Look into related descriptors and using a custom ManyToManyDescriptor for Addresses to Contacts to make sure that Address always comes prepopulated with the 'archived' db field. As well as a custom object manager.
- Maybe more effort that it's worth, but attach vcard to email / sms / whatsapp message
- Add a site-wide button which hides archived items from all views.
- Allow importing of contacts from .vcf files.
- Determine how to deal with Address / AddressType issue. i.e. an Address can have AddressType of 'PREF'... but that doesn't specify which Contact the Address is the preferred for. Maybe AddressType should be related to ContactAddress instead? Not a big deal though. Sort it later.
- Find out why profession seems to get overridden by email address when scanning qr code on iphone.
- vcard object for setting / getting properties of a vcard? Useful for import / export


### Handy Links

- [vCard docs](https://en.wikipedia.org/wiki/VCard)
- [Django naming conventions](https://stackoverflow.com/questions/31816624/naming-convention-for-django-url-templates-models-and-views)
- [Setting up a django project with pipenv](https://python.plainenglish.io/setting-up-a-basic-django-project-with-pipenv-7c58fa2ec631)
- [Creating a vcard qrcode in python](https://www.joshfinnie.com/blog/creating-a-vcard-qr-code-in-python/)
- [Countries with regional codes](https://github.com/lukes/ISO-3166-Countries-with-Regional-Codes/blob/master/all/all.csv)