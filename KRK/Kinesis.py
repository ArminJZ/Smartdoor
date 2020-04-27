import boto3
import time

def createCollection(collection_id):
    client = boto3.client('rekognition')

    # Create a collection
    response = client.create_collection(CollectionId=collection_id)
    return response['CollectionArn']

def createStreamProcessor(kvs_arn, kds_arn, name, collection_id, role_arn):
    client = boto3.client("rekognition")
    response = client.create_stream_processor(
        Input={
            'KinesisVideoStream': {
                'Arn': kvs_arn
            }
        },
        Output={
            'KinesisDataStream': {
                'Arn': kds_arn
            }
        },
        Name=name,
        RoleArn=role_arn,
        Settings={
            'FaceSearch': {
                'CollectionId': collection_id,
                "FaceMatchThreshold": 1.0
            }
        },
    )

    return response

def statusStreamProcessor(name):
    client = boto3.client("rekognition")
    response = client.describe_stream_processor(
        Name=name
    )
    print(response)
    return response


def startStreamProcessor(name):
    client = boto3.client("rekognition")
    response = client.start_stream_processor(
        Name=name
    )
    print("Start the stream processor")
    return response

def stopStreamProcessor(name):
    client = boto3.client("rekognition")
    response = client.stop_stream_processor(
        Name=name
    )
    print("Stream processor stopped!")
    return response

def deleteStreamProcessor(name):
    client = boto3.client("rekognition")
    response = client.delete_stream_processor(
        Name=name
    )
    print(response)
    print("Deletion completed!")
    return response

def listStreamProcessors():
    client = boto3.client("rekognition")
    response = client.list_stream_processors(
    )
    print(response)
    return response




# def lambda_handler(event, context):
if __name__ == "__main__":
    # TODO implement

    """
    Process Video Streams with Rekognition, output to KDS
    """

    # *** Have to replace event object with test cases after this

    collection_id = "known-visitors"
    kvs_arn = "arn:aws:kinesisvideo:us-east-1:584092006642:stream/kvs_smartdoor/1587838980687"
    kds_arn = "arn:aws:kinesis:us-east-1:584092006642:stream/kds_smartdoor"
    role_arn = "arn:aws:iam::584092006642:role/KRNK"
    stream_process_name = "smartdoor_processor"

    # stopStreamProcessor(stream_process_name)
    # deleteStreamProcessor("smartdoor")
    # listStreamProcessors()


    createStreamProcessor(kvs_arn, kds_arn, stream_process_name, collection_id, role_arn)

    startStreamProcessor(stream_process_name)

    for i in range(5):
        statusStreamProcessor(stream_process_name)
        time.sleep(5)

    status = statusStreamProcessor(stream_process_name)
    if status["Status"] == "RUNNING":
        stopStreamProcessor(stream_process_name)

    deleteStreamProcessor(stream_process_name)



