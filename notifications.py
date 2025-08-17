from twilio.rest import Client

def send_notification(user_id, message):
    user = User.query.get(user_id)
    if user.phone:
        client = Client('your_twilio_account_sid', 'your_twilio_auth_token')
        client.messages.create(
            body=message,
            from_='+1234567890',
            to=user.phone
        )
    if user.email:
        # Send email using SendGrid or SMTP
        pass