import boto3

ses = boto3.client("ses")

Message_details = "These is a unknown visitor. Please verify his identity."
Message_photo = "https://visitors-face.s3.amazonaws.com/known_visitor_1.jpg"


response = ses.send_email(
    Source='woodenrubberzhang@gmail.com',
    Destination={
        'ToAddresses': [
            'woodenrubberzhang@gmail.com',
        ]
    },
    Message={
        'Subject': {
            'Data': 'Unkown visitor'
        },
        'Body': {
            'Html': {
                'Data': Message_details + Message_photo
            }
        }
    }
)