from __future__ import print_function
import boto3
import time
import base64



rek = boto3.client('rekognition')
sns = boto3.client('sns')
kinesis = boto3.client('kinesis')


def createCollection(collection_id):
    client = boto3.client('rekognition')

    # Create a collection
    response = client.create_collection(CollectionId=collection_id)
    return response['CollectionArn']

def addKnownVisitors(bucket, photo, collection_id):
    client = boto3.client('rekognition')

    response = client.index_faces(CollectionId=collection_id,
                                  Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
                                  ExternalImageId=photo,
                                  MaxFaces=1,
                                  QualityFilter="AUTO",
                                  DetectionAttributes=['ALL'])

    for _ in response['FaceRecords']:
        face_id = response['Face']['FaceId']

    for unindexed_faces in response['UnindexedFaces']:
        reasons = response['Reasons']
        print("The face is failed to be indexed. The reason for it is {}".format(reasons))


def startFaceDetection():
    response = rek.start_face_detection(
        Video={
            'S3Object': {
                'Bucket': 'rzrekogtest',
                'Name': 'Movie on 4-11-20 at 9.36 PM.mov',
                # 'Version': 'string'
            }
        },
        # ClientRequestToken='string',
        NotificationChannel={
            'SNSTopicArn': 'arn:aws:sns:us-east-1:971614317796:face_detection',
            'RoleArn': 'arn:aws:iam::971614317796:role/rekg-to-sns'
        },
        # FaceAttributes = 'ALL',
        # JobTag='faceDetection'
    )

    return response['JobId']


def getFaceDetectionResult(job_id):
    max_result = 10
    succeeded = False

    response = rek.get_face_detection(
        JobId=job_id,
        MaxResults=max_result
    )

    while response['JobStatus'] == "IN_PROGRESS":
        print(response)
        time.sleep(5)
        response = rek.get_face_detection(
            JobId=job_id,
            MaxResults=max_result
        )

    if response['JobStatus'] == "FAILED":
        print("NO FACE DETECTED!")
        return

    print(response)


def createCollection(collection_id):
    client = boto3.client('rekogition')

    # Create a collection
    response = client.create_collection(CollectionId=collection_id)
    return response['CollectionArn']

    



# def lambda_handler(event, context):
#
#     job_id = startFaceDetection()
#
#     getFaceDetectionResult(job_id)

    # output = []
    # success = 0
    # failure = 0
    # for record in event['records']:
    #     try:
    #         # Uncomment the below line to publish the decoded data to the SNS topic.
    #         #payload = base64.b64decode(record['data'])
    #         #client.publish(TopicArn=topic_arn, Message=payload, Subject='Sent from Kinesis Analytics')
    #         output.append({'recordId': record['recordId'], 'result': 'Ok'})
    #         success += 1
    #     except Exception:
    #         output.append({'recordId': record['recordId'], 'result': 'DeliveryFailed'})
    #         failure += 1
    #
    # print('Successfully delivered {0} records, failed to deliver {1} records'.format(success, failure))
    # return {'records': output}
