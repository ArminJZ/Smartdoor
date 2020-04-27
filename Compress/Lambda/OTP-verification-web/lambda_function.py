import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

def lambda_handler(event, context):
    # TODO implement

    code = int(event['otp'])
    print(code)
    dynamodb = boto3.resource('dynamodb')
    passcode_table = dynamodb.Table('passcodes')
    visitor_table = dynamodb.Table('visitors')
    otp = passcode_table.scan(FilterExpression=Attr('passcode').eq(code))

    # If not matched, then means the input OTP is wrong.
    print(otp)
    if not otp['Items']:
        return {
            'pass': False
        }
    else:
        # If has the passcode is correct

        original_time = datetime.strptime(otp['Items'][0]['timeStamp'], "%m-%d-%Y %H:%M:%S")
        current_time = datetime.now()
        seconds = (current_time - original_time).total_seconds()
        minutes = divmod(seconds, 60)[0]

        # If excess the default timeout, then return false
        if minutes > 5:
             return {
                'pass': False
                #timeout
            }
            
        print("The One-Time Passcode is " + otp['Items'][0]['passcode'])
        
        items = passcode_table.scan(FilterExpression=Attr('passcode').eq(code))
        faceId = otp['Items'][0]['faceId']
        
        print(items['Items'][0]['faceId'])
        visitor_tuple = visitor_table.scan(FilterExpression=Attr('faceId').eq(faceId))
        #print(name)
    
        return {
            'pass': True,
            'data': {
                'name': visitor_tuple['Items'][0]['name']
            }

        }