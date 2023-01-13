import boto3
import json

# number -> str -> +972XXXXXXXXX ,  message -> str
def send_sms(number, message):
    client = boto3.client('lambda', region_name="eu-west-1")
    payload = { "number": number,"message":message } 
    result = client.invoke(FunctionName="sns-notification",
                InvocationType='Event',                                      
                Payload=json.dumps(payload))
    return result

