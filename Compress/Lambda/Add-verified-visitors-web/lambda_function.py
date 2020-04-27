import boto3
import json
from datetime import datetime
import random
from boto3.dynamodb.conditions import Key, Attr
"""
This file is to add the verified visitor into database and collections and send otp to them
"""

# import cv2      # *** Before upload to lambda function, I have to install the dependencies on the local path

def detectFaces(bucket, photo):
    client = boto3.client('rekognition')

    response = client.detect_faces(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': photo,
            }
        }
    )
    return response


def generate_otp(table):
    otp = int(random.random() * 1000000)
    passcode = table.scan(FilterExpression=Attr('otp').eq(otp))
    while passcode['Count']:
        otp = int(random.random() * 1000000)
        passcode = table.scan(FilterExpression=Attr('otp').eq(otp))
    return otp


def createCollection(collection_id):
    client = boto3.client('rekognition')

    # Create a collection
    response = client.create_collection(CollectionId=collection_id)
    print("Collection {} is created!".format(collection_id))
    return response['CollectionArn']


def indexFaces(bucket, photo_key, collection_id):
    s3 = boto3.client('rekognition')

    response = s3.index_faces(
        CollectionId=collection_id,
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': photo_key,
            }
        },
        ExternalImageId=photo_key,
        QualityFilter="AUTO",
        DetectionAttributes=['ALL']
    )

    print("Face indexed into the collection!")
    print(response)


def checkCollectionExists(collection_id):
    client = boto3.client('rekognition')

    response = client.list_collections()

    collections = response['CollectionIds']

    print(response)
    if not collection_id in collections:
        print("No such collection exists! Create one!")
        return False
    else:
        print("Such collection exists")
        return True


def describeCollection(collection_id):
    client = boto3.client('rekognition')

    response = client.describe_collection(
        CollectionId=collection_id
    )
    return response

def listCollections():
    client = boto3.client('rekognition')

    response = client.list_collections(

    )

    return response


def sendSMS(message, phone_num):
    sns = boto3.client('sns')
    response = sns.publish(
        PhoneNumber=phone_num,
        Message=message,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
    )

    return response


def lambda_handler(event, context): # The event is from Web page
    # TODO implement

    """
    Add the face image to the collection called "faces-collection".
    """
    photo_key = event['pic']
    bucket_name = "visitors-face"
    collection_id = "faces-collection"

    if not checkCollectionExists(collection_id):
        createCollection(collection_id)

    face_index_response = indexFaces(bucket_name, photo_key, collection_id)

    print(describeCollection(collection_id))

    dynamodb = boto3.resource("dynamodb")
    passcode_table = dynamodb.Table('passcodes')
    visitor_table = dynamodb.Table('visitors')

    """
    Put this face information and relevant file into visitors table
    """
    faceRecord = face_index_response['FaceRecords'][0]
    faceId = faceRecord['Face']['FaceId']
    name = event['name']
    phone_num = event['phone']

    visitor_table.put_item(
        Item={
                'faceId': faceId,
                'name': name,
                'phoneNumber': phone_num,
                'photo': [
                    {
                        'objectKey': name,
                        'bucket': bucket_name,
                        'createdTimestamp': datetime.now().strftime("%m-%d-%Y %H:%M:%S")
                    }
                ]
        }
    )

    """
    Put the face id and passcode record into passcode table
    """
    otp = generate_otp(passcode_table)
    passcode_table.put_item(
    Item={
            'faceId': faceId,
            'passcode': otp,
            'timeStamp': datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        }
    )

    response_sns_text = 'Welcome! here is the one-time passcode: {} \nIt would be expired in 5 minutes!'.format(otp)

    response = sendSMS(response_sns_text, phone_num)


    print('sent otp')
    return {
        'pass': True,
    }







