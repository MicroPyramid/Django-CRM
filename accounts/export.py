import json
import re
import requests

from crm.settings import BASE_DIR
from crm.local_settings import REMOTE_USER, REMOTE_URL, REMOTE_PASSWORD


def export_to_easytrans(account, created=False, update_contacts=True):

    accountdict = json.load(open(BASE_DIR + '/crm/template.json'))
    contacts = account.contacts.all()

    # Split address on multiple lines.
    customeraddress = re.sub('[\w+-]+$', '', account.billing_street)
    if customeraddress[-1:] == ' ':
        customeraddress = customeraddress[:-1]
    customeraddressnr = re.search('[\w+-]+$', account.billing_street).group()

    # Setup Authentication
    accountdict['authentication']['username'] = REMOTE_USER
    accountdict['authentication']['password'] = REMOTE_PASSWORD

    # Setup Account
    accountdict['customers'][0]['customerno'] = account.id
    accountdict['customers'][0]['update_on_existing_customernr'] = True
    accountdict['customers'][0]['update_on_existing_customer_contacts'] = update_contacts
    accountdict['customers'][0]['company_name'] = account.name
    accountdict['customers'][0]['address'] = customeraddress
    accountdict['customers'][0]['houseno'] = customeraddressnr
    accountdict['customers'][0]['postal_code'] = account.billing_postcode
    accountdict['customers'][0]['city'] = account.billing_city
    accountdict['customers'][0]['country'] = account.billing_country
    accountdict['customers'][0]['email'] = account.email

    # Setup Contacts
    for contact in contacts:

        contact_dict = dict()
        contact_dict['contact_name'] = '%s %s'.format(contact.first_name, contact.last_name)
        contact_dict['telephone'] = contact.phone.as_international
        contact_dict['email'] = contact.email
        contact_dict['contact_remark'] = contact.description

        accountdict['customers'][0]['customer_contacts'].append(contact_dict)

    # Send to Easytrans API
    return requests.post(REMOTE_URL, {'json': json.dumps(accountdict, sort_keys=False, indent=4)})

# {
#   "comments": "EasyTrans Software JSON import format for customers",
#   "authentication": { \n
#     "username": "user1234", \n
#     "password": "abcd1234",
#     "type": "customer_import",
#     "mode": "test"
#   },
#   "customers": [
#     {
#       "company_name": "Example Company A",
#       "attn": "Administration",
#       "address": "Keizersgracht",
#       "houseno": "1",
#       "addition": "a",
#       "address2": "2nd floor",
#       "postal_code": "1015CC",
#       "city": "Amsterdam",
#       "country": "NL",
#       "mail_address": "Postbus",
#       "mail_houseno": "73",
#       "mail_addition": "",
#       "mail_address2": "",
#       "mail_postal_code": "1010AA",
#       "mail_city": "Amsterdam",
#       "mail_country": "NL",
#       "debtorno": "ABC1234",
#       "payment_ref": "Example project",
#       "website": "www.easytrans.nl",
#       "remark": "Customer remark",
#       "bicno": "INGBNL2A",
#       "ibanno": "NL63INGB0004511811",
#       "cocno": "50725769",
#       "vatno": "NL822891682B01",
#       "vat_liable": 1,
# 		"language": "nl",
#       "customer_contacts": [
#         {
#           "salutation": 1,
#           "contact_name": "Bram Pietersen",
#           "telephone": "020-7654321",
#           "mobile": "06-12345678",
#           "email": "bram@easytrans.nl",
#           "contact_remark": "Warehouse manager",
#           "username": "bram",
#           "password": "v5xhCmRs"
#         },
#         {
#           "salutation": 2,
#           "contact_name": "Kim Verbeek",
#           "telephone": "020-7654321",
#           "mobile": "06-12345678",
#           "fax": "020-1234567",
#           "email": "kim@easytrans.nl",
#           "contact_remark": "Front desk",
#           "username": "kim",
#           "password": "eLn3y23D"
#         }
#       ]
#     },
#     {
#       "customerno": 12345,
#       "update_on_existing_customerno": true,
# 		"delete_existing_customer_contacts": true,
#       "company_name": "Example Company B",
#       "attn": "Administration",
#       "address": "Kanaalweg",
#       "houseno": "14",
#       "addition": "",
#       "address2": "",
#       "postal_code": "3526KL",
#       "city": "Utrecht",
#       "country": "NL",
#       "mail_address": "Steenstraat",
#       "mail_houseno": "17",
#       "mail_addition": "bis",
#       "mail_address2": "",
#       "mail_postal_code": "6828CA",
#       "mail_city": "Arnhem",
#       "mail_country": "NL",
#       "debtorno": "",
#       "payment_ref": "007896",
#       "website": "www.easytrans.nl",
#       "remark": "Customer remark",
#       "bicno": "INGBNL2A",
#       "ibanno": "NL63INGB0004511811",
#       "cocno": "50725769",
#       "vatno": "NL822891682B01",
#       "vat_liable": 1,
# 		"language": "en",
#       "customer_contacts": [
#         {
#           "salutation": 0,
#           "contact_name": "Klaassen",
#           "telephone": "026-34567891",
#           "mobile": "",
#           "fax": "026-1234567",
#           "email": "service@easytrans.nl",
#           "contact_remark": "",
#           "username": "klaassen",
#           "password": "a2451V0w"
#         }
#       ]
#     }
#   ]
# }