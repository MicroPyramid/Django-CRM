from django.dispatch import Signal

# The following fields are used from the 3 signals below: mail_obj, bounce_obj, raw_message
bounce_received = Signal()
complaint_received = Signal()
delivery_received = Signal()
send_received = Signal()
open_received = Signal()
click_received = Signal()
