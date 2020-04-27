import boto3

client = boto3.client("rekognition")


# print(client.delete_collection(CollectionId="faces-collection"))
# print(client.create_collection(CollectionId="known-visitors"))
# print(client.list_collections())


#
print(client.index_faces(
    CollectionId="known-visitors", Image={
        'S3Object': {
            'Bucket': 'smartdoorvisitorphoto',
            'Name': 'visitor_1.jpg',
        }
    },

    QualityFilter='HIGH'))

# print(client.describe_collection(CollectionId="known-visitors"))

# print(client.search_faces_by_image(CollectionId="known-visitors", Image={
#         'S3Object': {
#             'Bucket': 'visitors-face',
#             'Name': 'visitor_11.jpg',
#         }
# }))