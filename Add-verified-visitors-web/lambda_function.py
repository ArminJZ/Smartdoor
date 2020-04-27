import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import random


def add_faces_to_collection(bucket, photo, collection_id):
    client = boto3.client('rekognition')

    response = client.index_faces(CollectionId=collection_id,
                                  Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                  )

    print('Results for ' + photo)
    print('Faces indexed:')
    for faceRecord in response['FaceRecords']:
        print('  Face ID: ' + faceRecord['Face']['FaceId'])
        print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))

    print('Faces not indexed:')
    for unindexedFace in response['UnindexedFaces']:
        print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
        print(' Reasons:')
        for reason in unindexedFace['Reasons']:
            print('   ' + reason)

    return response['FaceRecords']


def generate_otp(table):
    otp = int(random.random() * 1000000)
    passcode = table.scan(FilterExpression=Attr('otp').eq(otp))
    while passcode['Count']:
        otp = int(random.random() * 1000000)
        passcode = table.scan(FilterExpression=Attr('otp').eq(otp))
    return otp


def send_sns(message, phone_num):
    messagingClient = boto3.client('sns')
    response = messagingClient.publish(
        PhoneNumber=phone_num,
        Message=message,
        MessageStructure='string',
    )
    return response


def lambda_handler(event, context):
    # TODO implement
    print(event['pic'])
    photo = event['pic']
    bucket = 'smartdoorvisitorphoto'
    collection_id = 'known-visitors'

    indexed_faces = add_faces_to_collection(bucket, photo, collection_id)

    dynamodb = boto3.resource('dynamodb')
    passcode_table = dynamodb.Table('passcodes')
    visitor_table = dynamodb.Table('visitors')

    # indexed face in such pic
    # for faceRecord in indexed_faces:
    faceRecord = indexed_faces[0]
    faceId = faceRecord['Face']['FaceId']
    name = event['name']
    phone_num = event['phone']

    print(faceId)
    visitor_table.put_item(
        Item={
            'faceId': faceId,
            'name': name,
            'phoneNumber': phone_num,
            'photo': [
                {
                    # 'objectKey': photo,
                    'bucket': bucket,
                    'createdTimestamp': datetime.now().strftime("%m-%d-%Y %H:%M:%S")
                }
            ]
        }
    )
    print("insert to visitor_table")

    otp = generate_otp(passcode_table)
    passcode_table.put_item(
        Item={
            'faceId': faceId,
            'passcode': otp,
            'timeStamp': datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        }
    )
    print("insert to passcode_table")

    response_sns_text = 'Here is your one-time passcode: {otp} \nIt will expire in 5 minutes.\n'.format(
        otp=otp
    )
    response = send_sns(response_sns_text, phone_num)
    print("sent otp")
    return {
        'pass': True,
    }

    return "end"