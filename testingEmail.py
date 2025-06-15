# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import os
from dotenv import load_dotenv

from email_sender import create_email
load_dotenv()
import traceback

email_sender = create_email(
    name="Sultan Rasul",
    breakdown_html_rows="breakdown_html_rows",
    clientPrice="1000",
    booking_reference="13452345",
    date_from="01/01/01",
    date_to="01/01/01",
    apartmentName="Emperor Apartment 1",
    phone="07928442268",
    adults=1,
    children=0,
    childrenAges=[],
    nights=2,
    refundable=False,
    email="sultanrasul5@gmail.com",
    specialRequests="",
    cancel=True
)

email_sender.send_email(os.getenv('email'))


print("what is good buddy")