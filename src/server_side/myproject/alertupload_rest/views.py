from alertupload_rest.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from twilio.rest import Client
from threading import Thread
import re
from django.conf import settings

# Thread decorator definition
def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_alert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        identify_email_sms(serializer)
    else:
        return JsonResponse({'error': 'Unable to process data!'}, status=400)
    
    return Response({
        'auth_token': request.META.get('HTTP_AUTHORIZATION'),
        'population_count': serializer.data.get('population_count')
    })

# Identifies if the user provided an email or a mobile number
def identify_email_sms(serializer):
    alert_receiver = serializer.data['alert_receiver']

    if re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}(\.\w{2,3})?$', alert_receiver):
        print("Valid Email")
        send_email(serializer)
    elif re.compile("^07\d{9}$").match(alert_receiver):
        print("Valid Mobile Number")
        send_sms(serializer)
    else:
        print("Invalid Email or Mobile number")

# Sends email
@start_new_thread
def send_email(serializer):
    send_mail(
        'Attention: High Traffic Detected!', 
        prepare_alert_message(serializer), 
        'objectdetectiontestemail@gmail.com',
        [serializer.data['alert_receiver']],
        fail_silently=True,
    )

# Sends SMS
@start_new_thread
def send_sms(serializer):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    phone_number = serializer.data['alert_receiver']
    if phone_number.startswith("07"):
        phone_number = "+44" + phone_number[1:]

    try:
        message = client.messages.create(
            body=prepare_alert_message(serializer),
            from_=settings.TWILIO_NUMBER,
            to=phone_number
        )
        print(f"SMS sent successfully to {phone_number}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

# Prepares the alert message
def prepare_alert_message(serializer):
    image_data = split(serializer.data['image'], ".")
    uuid = image_data[0]
    url = f'http://127.0.0.1:8000/alert{uuid}'

    return (
        f"Dear Traveler,\n\n"
        f"Our monitoring system has detected unusually high traffic in the airport. "
        f"To ensure a smooth experience, we recommend arriving at the airport 2-3 hours before your flight.\n\n"
        f"For more details, please visit: {url}\n\n"
        f"Thank you for your cooperation.\n\n"
        f"Safe travels,\n"
        f"Airport Management Team"
    )

# Splits string into a list
def split(value, key):
    return str(value).split(key)
