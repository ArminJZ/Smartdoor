import boto3
import json
import cv2
import base64
import random
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr


def generate_otp(table):
    otp = int(random.random() * 1000000)
    passcode = table.scan(FilterExpression=Attr('otp').eq(otp))
    while passcode['Count']:
        otp = int(random.random() * 1000000)
        passcode = table.scan(FilterExpression=Attr('otp').eq(otp))
    return otp


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


def getOjectfromS3(bucket, key):
    s3 = boto3.client("s3")

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )
    return response


def lambda_handler(event, context):
    # TODO implement

    """
    read the object from Kinesis Data Streams
    """
    for each_record in event['Records']:
        # The data is encoded by base64. Decode it first
        payload = json.loads(base64.b64decode(each_record['kinesis']['data']))
        print(payload)

        dynamodb = boto3.resource('dynamodb')
        passcode_table = dynamodb.Table('passcodes')
        visitor_table = dynamodb.Table('visitors')

        # If FaceSearchResponse and MatchedFaces exists, the video can find the face matching with collections
        if payload['FaceSearchResponse']:
            face_search_response = payload['FaceSearchResponse']
            print(face_search_response)
            if face_search_response[0]['MatchedFaces']:

                print("Video visitor's face is matched. This is a known visitors.")

                match_faces = face_search_response[0]['MatchedFaces']
                similarity = match_faces[0]['Similarity']
                faceId = match_faces[0]['Face']['FaceId']

                # Send otp to verify his
                otp = generate_otp(passcode_table)
                passcode = passcode_table.scan(FilterExpression=Attr('faceId').eq(faceId))

                # If this passcode is already exists, means it is still in verification process
                if passcode['Items']:
                    original_time = datetime.strptime(passcode['Items'][0]['timeStamp'], "%m-%d-%Y %H:%M:%S")
                    current_time = datetime.now()
                    seconds = (current_time - original_time).total_seconds()
                    minutes = divmod(seconds, 60)[0]

                    # If the message is expired, update the database
                    if minutes > 5:
                        print("update the item in database Now!")
                        passcode_table.update_item(
                            Key={
                                'faceId': faceId,
                            },
                            AttributeUpdates={
                                'passcode': {
                                    'Value': otp,
                                    'Action': 'PUT'
                                },
                                'timeStamp': {
                                    'Value': current_time.strftime("%m-%d-%Y %H:%M:%S"),
                                    'Action': 'PUT'
                                }
                            }
                        )

                    # If it is still in 5 minutes, We just wait
                    else:
                        continue

                # If the verification process is not started, we start it at once
                else:
                    passcode_table.put_item(
                        Item={
                            'faceId': faceId,
                            'passcode': otp,
                            'timeStamp': datetime.now().strftime("%m-%d-%Y %H:%M:%S")
                        }
                    )

                visitor = visitor_table.scan(FilterExpression=Attr('faceId').eq(faceId))

                print("Visitors database retrieved information is {}".format(visitor))

                phone_num = visitor['Items'][0]['phoneNumber']

                print("Phone number is {}".format(phone_num))
                response_sns_text = 'Welcome! here is the one-time passcode: {} \nIt would be expired in 5 minutes!'.format(
                    otp)

                response = sendSMS(response_sns_text, phone_num)
                print(response)

                return response


            else:  # If there is no matched face in the collection

                """
                Verify unknown visitors
                """

                print("The visitor is not a known visitor.")

                FragmentNumber = payload['InputInformation']['KinesisVideo']['FragmentNumber']

                kvs = boto3.client('kinesisvideo')
                data_endpoint = kvs.get_data_endpoint(
                    StreamARN="arn:aws:kinesisvideo:us-east-1:584092006642:stream/smartdoor_kvs/1587833103577",
                    APIName="GET_MEDIA"
                )

                print("Data endpoint is {}".format(data_endpoint))

                endpoint = data_endpoint['DataEndpoint']

                kvs_video = boto3.client('kinesis-video-media', endpoint_url=endpoint)
                kvs_stream = kvs_video.get_media(
                    StreamARN="arn:aws:kinesisvideo:us-east-1:584092006642:stream/smartdoor_kvs/1587833103577",
                    StartSelector={
                        'StartSelectorType': 'FRAGMENT_NUMBER', 'AfterFragmentNumber': FragmentNumber
                    }
                )
                print("kvs_stream information is {}".format(kvs_stream))

                file_path = '/tmp/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.mkv'
                image_name = datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.jpg'
                image_path = '/tmp/' + image_name

                with open('/tmp/stream.mkv', 'wb') as f:
                    streamBody = kvs_stream['Payload'].read(
                        1024 * 2048)  # reads min(16MB of payload, payload size) - can tweak this
                    f.write(streamBody)
                f.close()

                """
                # Use OpenCV to get a frame from the video
                """

                # use openCV to get a frame
                print("write video to tmp")

                cap = cv2.VideoCapture('/tmp/stream.mkv')
                print("capture with cv2")

                # use some logic to ensure the frame being read has the person, something like bounding box or median'th frame of the video etc
                bucket_name = 'smartdoorvisitorphoto'
                photo_name = 'photo-' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S") + '.jpg'

                ret, frame = cap.read()
                print("read frame")

                if frame is None:
                    continue

                s3_client = boto3.client('s3')

                all_objects = s3_client.list_objects(Bucket=bucket_name)['Contents']

                timeNow = datetime.now()
                threshold = 180

                canInsert = True

                for object in all_objects:
                    fileName = object['Key']
                    print(fileName)
                    if not fileName.startswith('photo'):
                        continue
                    original_time = datetime.strptime(fileName.split(".")[0][6:], "%m-%d-%Y-%H-%M-%S")
                    time_diff = (timeNow - original_time).total_seconds()
                    if (time_diff <= 180):
                        canInsert = False
                        break
                if not canInsert:
                    continue

                cv2.imwrite('/tmp/frame.jpg', frame)
                print("write frame to tmp")

                s3_client.upload_file(
                    '/tmp/frame.jpg',
                    bucket_name,
                    photo_name
                )
                cap.release()

                """
                # Send the email notification to the owner
                """

                ses = boto3.client("ses")

                Message_details = "These is a unknown visitor. Please verify his identity."
                Message_photo = "https://smartdoorvisitorphoto.s3.amazonaws.com/{}".format(photo_name)


                response = ses.send_email(
                    Source='woodenrubberzhang@gmail.com',
                    Destination={
                        'ToAddresses': [
                            'woodenrubberzhang@gmail.com',
                        ]
                    },
                    Message={
                        'Subject': {
                            'Data': 'Unknown visitor'
                        },
                        'Body': {
                            'Html': {
                                'Data': Message_details + Message_photo
                            }
                        }
                    }
                )
                print("Image uploaded!")
                print("SES response is {}".format(response))
                return response

        return "No face detected!"
    return "That is an end!"








