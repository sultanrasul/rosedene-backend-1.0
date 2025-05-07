# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import os
from dotenv import load_dotenv
load_dotenv()
import traceback


message = Mail(
    from_email='booking@rosedenedirect.com',
    to_emails='sultanrasul5@gmail.com',
    subject=f'Confirmation of your reservation: Rosedene Highland House No.143065566',
    html_content='''
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {
            font-family: "Calibri", sans-serif;
        }
        /* Reset styles for email clients */
        .main-table { width: 100% !important; max-width: 600px !important; margin: 0 auto !important; }
        img { border: 0; line-height: 100%; max-width: 100% !important; }
        .mobile-stack { display: block !important; width: 100% !important; }
        .separator { border-left: 1px solid #cccccc; height: 40px; }
        .data-row { padding: 12px 0; border-top: 1px solid #e2e8f0; }
        
        @media screen and (max-width: 600px) {
            .main-table, .mobile-stack { width: 100% !important; }
            td.mobile-stack { display: block !important; width: 100% !important; }
            .desktop-hide { display: none !important; }
            .mobile-center { text-align: center !important; }
            .mobile-pad { padding: 10px !important; }
            .mobile-text { font-size: 14px !important; }
            .mobile-header { font-size: 20px !important; }
            img { height: auto !important; max-height: 300px !important; }
        }
    </style>
    </head>
    <body style="margin:0; padding:20px 0; background:#f5f5f5;">

    <!-- Wrapper Table -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center">
                <!-- Main Container -->
                <table class="main-table" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">
                    <!-- Email Details Section -->
                    <tr>
                        <td style="padding:10px; text-align:center;">
                            <p style="color:#2d3748; font-size:12px; margin:8px 0 30px;text-align:center;">
                                IMPORTANT: This confirmation email has been generated automatically, so please do not reply to this address. To view or cancel your reservation, please go to the "Find Details" section of our website and quote the confirmation or reservation number shown in this email.
                            </p>
                            <img src="https://rosedenedirect.com/logo.png" alt="Rosedene Logo" style="width:90%; max-width:200px; margin:0 auto 30px; display:block;">
                            
                            <!-- Email Content -->
                            <table width="100%" style="border:1px solid #e2e8f0; border-radius:12px; background:#ffffff; padding:20px; text-align:left;margin-bottom:90px;">
                                <tr>
                                    <td>
                                        <p>
                                            Dear Mr Rasul,
                                        </p>
                                        <p>
                                            Thank you for choosing 
                                            <span style="color:#C09A5B;font-weight:bold;">Rosedene Highland House</span>
                                            for your next stay in 
                                            <span style="color:#C09A5B;font-weight:bold;">Inverness</span>.
                                        </p>
                                        <p>
                                            Please see below for details of your reservation.
                                        </p>
                                        <p>
                                            We hope you enjoy your stay!
                                        </p>
                                        <p>
                                            Kind regards,<br>
                                            ALL – Accor Live Limitless Customer Service
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Green Checkmark Section -->
                    <tr>
                        <td style="padding:10px; text-align:center;">
                            <table width="100%" style="margin:-0px auto 0;">
                                <tr>
                                    <td align="center">
                                        <div style="width:80px; height:80px; background:#ffffff; border-radius:50%;">
                                            <img src="https://cdn-icons-png.flaticon.com/512/5610/5610944.png" alt="Payment Successful" style="width:100%; height:auto; display:block;">
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Booking Details Section -->
                    <tr>
                        <td style="padding:10px; border-radius:12px;">
                            <table width="100%">
                                <tr>
                                    <td style="text-align:center; padding-bottom:20px;">
                                        <h1 style="color:#C09A5B; font-size:32px; margin:0;padding-top:0px;">
                                            Payment Successful!
                                        </h1>
                                        <p style="color:#666666; font-size:16px; margin:8px 0 0;">
                                            Your reservation is confirmed
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Details Card -->
                            <table width="100%" style="background:#f8fafc; border-radius:12px; border:1px solid #e2e8f0; padding:20px;">
                                <!-- Total Amount -->
                                <tr>
                                    <td style="padding-bottom:15px;">
                                        <table width="100%">
                                            <tr>
                                                <td style="color:#64748b; font-weight:500;">Total Amount</td>
                                                <td style="text-align:right; color:#1e293b; font-size:24px; font-weight:700;">£3600.00</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- Reference Number -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="color:#64748b;">Reference Number</td>
                                            <td style="text-align:right; color:#1e293b;">143065566</td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Apartment -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="color:#64748b;">Apartment</td>
                                            <td style="text-align:right; color:#1e293b;">The Cottage Apartment 10</td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Guest Info -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="color:#64748b;">Guest Name</td>
                                            <td style="text-align:right; color:#1e293b;">Sob</td>
                                        </tr>
                                        <tr><td colspan="2" style="padding-top:8px;"></td></tr>
                                        <tr>
                                            <td style="color:#64748b;">Email</td>
                                            <td style="text-align:right; color:#1e293b;">pukkapukka@hotmail.co.uk</td>
                                        </tr>
                                        <tr><td colspan="2" style="padding-top:8px;"></td></tr>
                                        <tr>
                                            <td style="color:#64748b;">Phone</td>
                                            <td style="text-align:right; color:#1e293b;">+447590235763</td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Dates -->
                                <tr><td class="data-row">
                                    <table width="100%">
                                        <tr>
                                            <td style="width:50%;">
                                                <div style="color:#64748b;">Check-in</div>
                                                <div style="color:#1e293b; font-weight:500;">17/02/2025</div>
                                            </td>
                                            <td style="width:0%; text-align:center;">
                                                <div class="separator"></div>
                                            </td>
                                            <td style="width:50%;text-align: right;">
                                                <div style="color:#64748b;">Check-out</div>
                                                <div style="color:#1e293b; font-weight:500;">20/02/2025</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td></tr>

                                <!-- Guest Details -->
                                <tr><td class="data-row">
                                        <table width="100%">
                                            <tr>
                                                <td style="width:33%; text-align: left;">
                                                    <div style="color:#64748b;">Adults</div>
                                                    <div style="color:#1e293b; font-weight:500;">2</div>
                                                </td>
                                                <td style="width:33%; text-align: center;">
                                                    <div style="color:#64748b;">Children</div>
                                                    <div style="color:#1e293b; font-weight:500;">2</div>
                                                </td>
                                                <td style="width:33%; text-align: right;">
                                                    <div style="color:#64748b;">Nights</div>
                                                    <div style="color:#1e293b; font-weight:500;">3</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td></tr>
                                
                                <!-- Children Ages -->
                                <tr>
                                    <td>
                                        <table width="100%">
                                            <tr>
                                                <td style="color:#64748b;">Children Ages</td>
                                                <td style="text-align:right; color:#1e293b;">1, 2 Year Old</td>
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
    </table>
    </body>
    </html>
    ''')
try:
    sg = SendGridAPIClient(os.getenv('email')+"testing")
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    traceback.print_exc()  # full error trace

print("what is good buddy")