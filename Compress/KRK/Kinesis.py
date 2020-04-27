import boto3
import time


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

    collection_id = "faces-collection"
    kvs_arn = "arn:aws:kinesisvideo:us-east-1:971614317796:stream/smartdoorkvs/1587152393750"
    kds_arn = "arn:aws:kinesis:us-east-1:971614317796:stream/smartdoorkds"
    role_arn = "arn:aws:iam::971614317796:role/KRK"
    stream_process_name = "smartdoor"


    createStreamProcessor(kvs_arn, kds_arn, stream_process_name, collection_id, role_arn)

    startStreamProcessor(stream_process_name)

    for i in range(3):
        statusStreamProcessor(stream_process_name)
        time.sleep(5)

    status = statusStreamProcessor(stream_process_name)
    if status["Status"] == "RUNNING":
        stopStreamProcessor(stream_process_name)

    deleteStreamProcessor(stream_process_name)






