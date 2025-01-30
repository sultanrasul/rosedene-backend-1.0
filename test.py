import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Your SendGrid SMTP credentials
smtp_server = 'smtp.sendgrid.net'
smtp_port = 587
username = 'apikey'  # Use 'apikey' as the username
password = "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"

# Email details
from_email = 'booking@booking.funkypanda.dev'  # Your verified email address
to_email = 'sultanrasul5+me@gmail.com'  # Recipient email address
subject = 'Test Email'
body = 'This is a test email sent via SendGrid SMTP using Python!'

# Create the email message
msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = subject

html_content = '''
<div style="background-color: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); padding-top: 40px; padding-bottom: 30px; padding-left: 30px; padding-right: 30px; max-width: 600px; width: 100%; color: black; position: relative;">
    
    <!-- Payment Success Text -->
    <h1 style="text-align: center; color: #2D3748; font-size: 24px; font-weight: 600;">Payment Success!</h1>
    <p style="text-align: center; color: #6B7280; margin-top: 8px;">Your Reservation has been complete</p>

    <!-- Payment Details -->
    <div style="background-color: #F3F4F6; border-radius: 10px; padding: 24px; margin-top: 24px;">
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr>
                <td style="color: #6B7280; text-align: left;">Amount</td>
                <td style="text-align: right; color: #2D3748; font-weight: 500; font-size: 18px;">£500.00</td>
            </tr>
            <tr>
                <td style="color: #6B7280; text-align: left;">Ref Number</td>
                <td style="text-align: right; color: #2D3748;">23452345</td>
            </tr>
            <tr>
                <td style="color: #6B7280; text-align: left;">Apartment</td>
                <td style="text-align: right; color: #2D3748;">Emperor Studio Apartment 3</td>
            </tr>
            <tr>
                <td style="color: #6B7280; text-align: left;">Name</td>
                <td style="text-align: right; color: #2D3748;">Sultan Rasul</td>
            </tr>
            <tr>
                <td style="color: #6B7280; text-align: left;">Email</td>
                <td style="text-align: right; color: #2D3748;">Sultan Rasul</td>
            </tr>
            <tr>
                <td style="color: #6B7280; text-align: left;">Phone Number</td>
                <td style="text-align: right; color: #2D3748;">07928468825</td>
            </tr>
        </table>

        <hr style="height: 1px; margin: 8px 0; background-color: #D1D5DB; border: none;">

        <!-- Check-in and Check-out -->
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr>
                <td style="color: #6B7280; text-align: left;">Check-in</td>
                <td style="text-align: left; color: #2D3748;">30/01/2025</td>
                <td style="text-align: left; width: 20px; border-left: 1px solid #D1D5DB;"></td>
                <td style="color: #6B7280; text-align: left;">Check-out</td>
                <td style="text-align: right; color: #2D3748;">02/02/2025</td>
            </tr>
        </table>

        <hr style="height: 1px; margin: 8px 0; background-color: #D1D5DB; border: none;">

        <!-- Adults, Children, Nights -->
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr>
                <td style="color: #6B7280; text-align: left;">Adults</td>
                <td style="text-align: left; color: #2D3748;">2</td>
                <td style="text-align: left; width: 20px; border-left: 1px solid #D1D5DB;"></td>
                <td style="color: #6B7280; text-align: left;">Children</td>
                <td style="text-align: left; color: #2D3748;">2</td>
                <td style="text-align: left; width: 20px; border-left: 1px solid #D1D5DB;"></td>
                <td style="color: #6B7280; text-align: left;">Nights</td>
                <td style="text-align: right; color: #2D3748;">3</td>
            </tr>
        </table>

        <hr style="height: 1px; margin: 8px 0; background-color: #D1D5DB; border: none;">

        <!-- Children Ages -->
        <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
            <tr>
                <td style="color: #6B7280; text-align: left;">Children Ages</td>
                <td style="text-align: right; color: #2D3748;">1 and 2 Years Old</td>
            </tr>
        </table>
    </div>
</div>

'''

msg.attach(MIMEText(html_content, 'html'))


# Connect to the SendGrid SMTP server and send the email
try:
    # Establish a secure connection using TLS
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Encrypt the connection
    server.login(username, password)  # Log in using your API key as the password

    # Send the email
    server.sendmail(from_email, to_email, msg.as_string())
    print("Email sent successfully!")

except Exception as e:
    print(f"Failed to send email: {e}")

finally:
    server.quit()
