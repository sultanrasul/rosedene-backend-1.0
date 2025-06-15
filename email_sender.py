from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
import traceback

class create_email:
    def __init__(self, name, breakdown_html_rows, clientPrice, booking_reference , date_from, date_to,apartmentName, phone, adults, children, childrenAges, nights, refundable, email, specialRequests, cancel):
        self.name = name
        self.breakdown_html_rows = breakdown_html_rows
        self.clientPrice = clientPrice
        self.booking_reference = booking_reference
        self.apartmentName = apartmentName
        self.phone = phone
        self.date_from = date_from
        self.date_to = date_to
        self.adults = adults
        self.children = children
        self.childrenAges = childrenAges
        self.nights = nights
        self.refundable = refundable
        self.email = email
        self.specialRequests = specialRequests
        self.cancel = cancel

    def send_email(self, api_key):
        message = Mail(
            from_email='booking@rosedenedirect.com',
            to_emails=self.email,
            subject=f'Confirmation of your reservation: Rosedene Highland House No.{self.booking_reference}',
            html_content=self.create_html())
        try:
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            traceback.print_exc()  # full error trace


    def create_html(self):

        cancelled_html = f"""
            <tr>
                <td style="padding: 40px 0;">
                    <table width="100%" style="text-align: center;">
                        <tr>
                            <td align="center" style="padding-top:0px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:0px;">
                                <tr>
                                    <td align="center" style="width:80px; height:80px; background:#fee2e2; border-radius:50%; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                                    <table role="presentation" cellpadding="0" cellspacing="0">
                                        <tr>
                                        <td align="center" style="width:64px; height:64px; background:#ef4444; border-radius:50%;">
                                            <img src="https://rosedenedirect.com/email/x-white.png" width="40" height="40" alt="" style="display:block;">
                                        </td>
                                        </tr>
                                    </table>
                                    </td>
                                </tr>
                                </table>
                            </td>
                        </tr>
                    <tr>
                        <td style="padding-top: 20px;">
                        <h1 style="font-size: 28px; color: #dc2626; font-weight: bold; margin: 0;">Booking Cancelled</h1>
                        <p style="color: #6b7280; font-size: 16px; margin: 10px 0 0 0;">
                            This reservation has been cancelled.
                        </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding-top: 20px;">
                        {f'''
                        <p style="color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px; font-size: 14px; margin: 0 auto;">
                            Since your booking was made on a <strong>refundable rate</strong>, you will receive a refund within <strong>5–7 business days</strong>.
                        </p>
                        ''' if self.refundable else '''
                        <p style="color: #b91c1c; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 12px; font-size: 14px; margin: 0 auto;">
                            This booking was made on a <strong>non-refundable rate</strong>. Unfortunately, no refund will be issued.
                        </p>
                        '''}
                        </td>
                    </tr>
                    </table>
                </td>
            </tr>
        """ if self.cancel else f"""
            <!-- ✅ Payment Successful (only shown if NOT cancelled) -->
            <tr>
            <td style="padding: 40px 0;">
                <table width="100%" style="text-align: center;">
                <tr>
                    <td>
                    <div style="display: inline-block; background-color: #ecfdf5; border-radius: 9999px; padding: 12px; box-shadow: 0 0 12px rgba(0,0,0,0.1);">
                        <div style="width: 64px; height: 64px; background-color: #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                        <img src="https://rosedenedirect.com/email/check-green.png" width="28" height="28" alt="Success" />
                        </div>
                    </div>
                    </td>
                </tr>
                <tr>
                    <td style="padding-top: 20px;">
                    <h1 style="font-size: 28px; color: #047857; font-weight: bold; margin: 0;">Payment Successful</h1>
                    <p style="color: #6b7280; font-size: 16px; margin: 10px 0 0 0;">
                        Your booking has been confirmed.
                    </p>
                    </td>
                </tr>
                </table>
            </td>
            </tr>
        """

        special_requests_html = f"""
            <tr>
                <td style="padding-top: 20px;">
                    <p style="color:#6b7280; font-size:12px; font-weight:bold; margin:0 0 5px;">Special Requests</p>
                    <p style="height: 80px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; padding: 12px; margin: 0; width: 100%; box-sizing: border-box">
                        {self.specialRequests}
                    </p>
                </td>
            </tr>
        """ if self.specialRequests != "" else ""

        greeting_html = f"""
                    <table role="presentation" width="100%" style="background:#ffffff; border:1px solid #d1d5db; border-radius:12px; padding:20px; margin-bottom: 60px;" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="color:#000000; font-size:14px; line-height:1.5;">
                                <p style="margin:0 0 15px;">Dear {self.name},</p>
                                <p style="margin:0 0 15px;">We're sorry to hear that you've had to cancel your reservation at <span style="color:#C09A5B; font-weight:bold;">Rosedene Highland House</span>.</p>
                                <p style="margin:0 0 15px;">Your cancellation has been successfully processed. Below you'll find the details of your original reservation for your records.</p>
                                <p style="margin:0 0 15px;">We hope to welcome you in the future.</p>

                                <p style="margin:0;">Kind regards,<br>ALL - Rosedene Highland House Customer Service</p>
                            </td>
                        </tr>
                    </table>
                """ if self.cancel else f"""
                    <!-- Standard Welcome Message -->
                    <table role="presentation" width="100%" style="background:#ffffff; border:1px solid #d1d5db; border-radius:12px; padding:20px; margin-bottom: 60px;" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="color:#000000; font-size:14px; line-height:1.5;">
                                <p style="margin:0 0 15px;">Dear {self.name},</p>
                                <p style="margin:0 0 15px;">Thank you for choosing <span style="color:#C09A5B; font-weight:bold;">Rosedene Highland House</span> for your next stay in <span style="color:#C09A5B; font-weight:bold;">Inverness</span>.</p>
                                <p style="margin:0 0 15px;">Please see below for details of your reservation.</p>
                                <p style="margin:0 0 15px;">We hope you enjoy your stay!</p>
                                <p style="margin:0;">Kind regards,<br>ALL - Rosedene Highland House Customer Service</p>
                            </td>
                        </tr>
                    </table>
                """


        return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Booking Confirmation</title>
            <style>
                .view-details-btn {{
                    display: inline-block;
                    background-color: #C09A5B;
                    color: #ffffff !important;
                    font-weight: bold;
                    text-decoration: none;
                    text-align: center;
                    padding: 14px 28px;
                    border-radius: 8px;
                    font-size: 16px;
                    margin: 20px 0;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: background-color 0.3s ease;
                }}
                .view-details-btn:hover {{
                background-color: #a8834d;
                }}
                @media only screen and (max-width: 600px) {{
                .container {{
                    width: 100% !important;
                }}
                .logo-container {{}}
                .logo {{
                    max-width: 250px !important;
                    width: 100% !important;
                    height: auto !important;
                }}
                .full-width-mobile {{
                    width: 100% !important;
                }}
                .booking-details {{}}
                .booking-section {{}}
                .guest-info-section {{
                    display: block !important;
                    width: 100% !important;
                }}
                .guest-info-section td {{
                    padding-bottom: 20px !important;
                    display: block !important;
                    width: 100% !important;
                }}
                .guest-info-section td:last-child {{
                    padding-bottom: 0 !important;
                }}
                .guest-info-spacer {{
                    display: none !important;
                }}
                .two-column-layout {{
                    display: block !important;
                    width: 100% !important;
                }}
                .two-column-layout td {{
                    display: block !important;
                    width: 100% !important;
                    padding-bottom: 16px;
                }}
                .two-column-layout td:last-child {{
                    padding-bottom: 0;
                }}
                .full-name {{
                    width: 100% !important;
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                }}
                .footer {{
                    padding: 0 15px !important;
                }}
                .view-details-btn {{
                    display: block !important;
                    width: 100% !important;
                    box-sizing: border-box;
                }}
                }}
            </style>
            </head>
            <body style="-webkit-text-size-adjust: 100%; margin: 0; padding: 0; background-color: #f8fafc; font-family: Arial, Helvetica, sans-serif">
            <!--[if mso]>
                <table role="presentation" width="100%">
                <tr>
                <td style="padding:20px; background:#f8fafc;">
                <![endif]-->
            <center style="width:100%;">
                <table role="presentation" align="center" border="0" cellpadding="0" cellspacing="0" width="600" style="margin: 0 auto" class="container">
                <tr>
                    <td style="padding:45px 0 0;">
                    <table role="presentation" width="100%" class="logo-container" cellpadding="0" cellspacing="0">
                        <tr>
                        <td align="center">
                            <img src="https://rosedenedirect.com/logo.png" alt="Logo" width="300" class="logo" style="display: block; padding-bottom: 30px; max-width: 300px">
                        </td>
                        </tr>
                    </table>

                    {greeting_html}

                    <table role="presentation" width="100%" style="background: #ffffff; border: 1px solid #d1d5db; border-radius: 12px; margin-top: 20px; padding: 0 20px 20px" class="booking-details" cellpadding="0" cellspacing="0">
                        {cancelled_html}

                        <tr>
                        <td style="padding:20px 0;">
                            <table role="presentation" width="100%" style="border:1px solid #e5e7eb; border-radius:12px; padding:20px;" cellpadding="0" cellspacing="0">
                            <tr>
                                <td>
                                <h3 style="font-size:22px; color:#C09A5B; font-weight:bold; margin:0 0 15px;">Emperor Apartment 1</h3>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                        {self.breakdown_html_rows}
                                    </table>
                                    <hr style="border:none; border-top:1px solid #e5e7eb; margin:25px 0;">
                                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                        <td style="color:#C09A5B; font-weight:bold;">Total (GBP)</td>
                                        <td align="right" style="color:#C09A5B; font-weight:bold; font-size:22px;">£{self.clientPrice}</td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            </table>
                        </td>
                        </tr>
                        <tr>
                        <td style="padding: 10px 0" class="full-width-mobile">
                            <table role="presentation" width="100%" style="background:#F5F2ED; border:2px solid rgba(192,154,91,0.2); border-radius:12px; padding:15px;" cellpadding="0" cellspacing="0">
                            <tr>
                                <td width="60" align="center" valign="middle">
                                <table role="presentation" width="48" height="48" cellpadding="0" cellspacing="0" border="0" style="padding: 10px; background:#ffffff; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                                    <tr>
                                    <td align="center" valign="middle">
                                        <img width="32" height="32" src="https://rosedenedirect.com/email/ticket-check.png" alt style="display:block;">
                                    </td>
                                    </tr>
                                </table>
                                </td>
                                <td style="padding-left: 15px;">
                                <p style="color:#6b7280; font-size:12px; font-weight:bold; letter-spacing:1px; margin:0;">BOOKING REFERENCE</p>
                                <p style="color:#C09A5B; font-size:32px; font-weight:bold; margin:5px 0 0;">{self.booking_reference}</p>
                                </td>
                            </tr>
                            </table>
                        </td>
                        </tr>
                        <tr>
                            <td style="padding:10px 0;" class="full-width-mobile">
                                <table role="presentation" width="100%" style="background:#{'f0fdf4' if self.refundable else 'fdf2f2'}; border:{'2px solid #84e1bc' if self.refundable else '1px solid #f8b4b4'}; border-radius:12px;">
                                    <tr>
                                        <td style="padding:15px;">
                                            <table role="presentation" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td width="50" valign="top" align="center">
                                                        <table role="presentation" cellpadding="0" cellspacing="0">
                                                            <tr>
                                                                <td align="center" style="background:#{'bbf7d0' if self.refundable else 'fbd5d5'}; width:44px; height:44px; border-radius:50%; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                                                                    <img src="https://rosedenedirect.com/email/{'check-green.png' if self.refundable else 'x.png'}" width="20" height="20" alt="" style="display:block;">
                                                                </td>
                                                            </tr>
                                                        </table>
                                                    </td>
                                                    <td style="padding-left: 15px;">
                                                        <p style="color:#374151; font-size:14px; margin:0 0 5px 0;">Refundable Booking</p>
                                                        <p style="color:#6b7280; font-size:12px; margin:0;">
                                                            You are eligible for a refund if canceled 2 weeks before your check-in date.
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                        <td style="padding: 20px 0" class="booking-section">
                            <table role="presentation" width="100%" style="background:rgba(35,52,65,0.1); border-radius:12px; padding:20px;" cellpadding="0" cellspacing="0">
                            <tr>
                                <td>
                                <table role="presentation" width="100%" class="two-column-layout" cellpadding="0" cellspacing="0">
                                    <tr>
                                    <td width="50%" valign="top">
                                        <table role="presentation" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td valign="top" style="padding-bottom: 16px">
                                            <div style="display: inline-block; vertical-align: middle; margin-right: 12px">
                                                <div style="background:#ffffff; border-radius:12px; padding:12px; display:inline-block; box-shadow:0 4px 6px rgba(0,0,0,0.05); color:#4f46e5;">
                                                <img src="https://rosedenedirect.com/email/calendar.png" alt>
                                                </div>
                                            </div>
                                            <div style="display: inline-block; vertical-align: middle">
                                                <p style="color:#6b7280; font-size:0.875rem; line-height: 1.25rem; margin:0 0 5px;">Check-in</p>
                                                <p style="color:#000000; font-weight: 500; font-size:16px; margin:0;">{self.date_from}</p>
                                            </div>
                                            </td>
                                        </tr>
                                        </table>
                                    </td>
                                    <td width="50%" valign="top">
                                        <table role="presentation" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td valign="top" style="padding-bottom: 16px">
                                            <div style="display: inline-block; vertical-align: middle; margin-right: 12px">
                                                <div style="background:#ffffff; border-radius:12px; padding:12px; display:inline-block; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                                                <img src="https://rosedenedirect.com/email/calendar.png" alt>
                                                </div>
                                            </div>
                                            <div style="display: inline-block; vertical-align: middle">
                                                <p style="color:#6b7280; font-size:0.875rem; line-height: 1.25rem; margin:0 0 5px;">Check-out</p>
                                                <p style="color:#000000; font-weight: 500; font-size:16px; margin:0;">{self.date_to}</p>
                                            </div>
                                            </td>
                                        </tr>
                                        </table>
                                    </td>
                                    </tr>
                                </table>
                                </td>
                            </tr>
                            <tr>
                                <td height="15"></td>
                            </tr>
                            <tr>
                                <td>
                                <hr style="border:none; border-top:2px solid #d1d5db;">
                                </td>
                            </tr>
                            <tr>
                                <td height="15"></td>
                            </tr>
                            <tr>
                                <td>
                                <table role="presentation" width="100%" class="two-column-layout" cellpadding="0" cellspacing="0">
                                    <tr>
                                    <td width="50%" valign="top">
                                        <table role="presentation" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td valign="top">
                                                <div style="display: inline-block; vertical-align: middle; margin-right: 12px">
                                                    <div style="background:#ffffff; border-radius:12px; padding:12px; display:inline-block; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                                                    <img src="https://rosedenedirect.com/email/user-round.png" alt>
                                                    </div>
                                                </div>
                                                <div style="display: inline-block; vertical-align: middle">
                                                    <p style="color:#6b7280; font-size:0.875rem; line-height: 1.25rem; margin:0 0 5px;">Guests</p>
                                                    <p style="color:#000000; font-weight: 500; font-size:16px; margin:0;">
                                                        {self.adults} Adult{'s' if self.adults > 1 else ''} • {self.children} Child{'ren' if self.children > 1 else ''}
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                        </table>
                                    </td>
                                    <td width="50%" valign="top">
                                        <table role="presentation" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td valign="top">
                                                <div style="display: inline-block; vertical-align: middle; margin-right: 12px">
                                                    <div style="background:#ffffff; border-radius:12px; padding:12px; display:inline-block; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                                                    <img src="https://rosedenedirect.com/email/user-round.png" alt>
                                                    </div>
                                                </div>
                                                <div style="display: inline-block; vertical-align: middle">
                                                    <p style="color:#6b7280; font-size:0.875rem; line-height: 1.25rem; margin:0 0 5px;">Children Ages</p>
                                                        <p style="color:#000000; font-weight: 500; font-size:16px; margin:0;">
                                                            {', '.join(str(age) for age in self.childrenAges) if self.childrenAges else '0 Children'}
                                                            {'' if not self.childrenAges else '<span style="color:#6b7280; font-size:0.875rem; line-height: 1.25rem; font-weight:normal;">Years Old</span>'}
                                                        </p>
                                                </div>
                                            </td>
                                        </tr>
                                        </table>
                                    </td>
                                    </tr>
                                </table>
                                </td>
                            </tr>
                            </table>
                        </td>
                        </tr>
                        <tr>
                        <td>
                            <hr style="border:none; border-top:1px solid #c09a5b; margin:30px 0;">
                        </td>
                        </tr>
                        <tr>
                        <td class="booking-section">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td>
                                <h2 style="font-size:22px; color:#233441; font-weight:bold; margin:0 0 20px;">Guest information</h2>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                <table role="presentation" width="100%" style="margin-bottom:20px;" cellpadding="0" cellspacing="0">
                                    <tr>
                                    <td class="full-name">
                                        <p style="color:#6b7280; font-size:12px; font-weight:bold; margin:0 0 5px;">Full name</p>
                                        <p style="background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; padding: 12px; margin: 0; width: 100%; box-sizing: border-box">{self.name}</p>
                                    </td>
                                    </tr>
                                </table>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" class="guest-info-section">
                                    <tr>
                                    <td width="48%" valign="top" class="guest-info-section">
                                        <p style="color:#6b7280; font-size:12px; font-weight:bold; margin:0 0 5px;">Email</p>
                                        <p style="background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; padding: 12px; margin: 0; width: 100%; box-sizing: border-box">{self.email}</p>
                                    </td>
                                    <td width="4%" class="guest-info-spacer"></td>
                                    <td width="48%" valign="top" class="guest-info-section">
                                        <p style="color:#6b7280; font-size:12px; font-weight:bold; margin:0 0 5px;">Phone</p>
                                        <p style="background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; color: #6b7280; padding: 12px; margin: 0; width: 100%; box-sizing: border-box">{self.phone}</p>
                                    </td>
                                    </tr>
                                </table>
                                </td>
                            </tr>
                            <!-- Special Requests (Conditinal) -->
                            {special_requests_html}
                            </table>
                        </td>
                        </tr>
                        <tr>
                        <td align="center" style="padding-top:60px;">
                            <a target="_blank" href="https://rosedenedirect.com/details?ref_number={self.booking_reference}&email={self.email}" class="view-details-btn" style="transition: background-color 0.3s ease; display: inline-block; background-color: #C09A5B; font-weight: bold; text-decoration: none; text-align: center; padding: 14px 28px; border-radius: 8px; font-size: 16px; margin: 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #ffffff">
                            View & Manage Your Booking
                            </a>
                        </td>
                        </tr>
                    </table>
                    <table role="presentation" width="100%" style="margin-top: 20px" class="footer" cellpadding="0" cellspacing="0">
                        <tr>
                        <td align="center" style="padding:20px 0;">
                            <p style="color:#64748b; font-size:12px; margin:0;">
                            &copy; 2025 Boardbeach Ltd | All rights reserved
                            </p>
                        </td>
                        </tr>
                    </table>
                    </td>
                </tr>
                </table>
            </center> <!--[if mso]>
                </td>
                </tr>
                </table>
                <![endif]-->
            </body>
            </html>
        """
