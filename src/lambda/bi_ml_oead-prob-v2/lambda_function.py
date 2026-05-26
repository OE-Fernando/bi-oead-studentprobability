import os
import boto3
import json
import pandas as pd
import datetime

from data_srv_lambda import DataService
from data_contracts_lambda import build_calling_data
from holiday_service_lambda import HolidayService
from student_srv_lambda import StudentService

runtime = boto3.client('runtime.sagemaker')
s3_client = boto3.client('s3')

ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
bucket = os.environ['BUCKET']

prefix = 'oead-prob' # use this prefix to store all files
modelprefix = prefix + '/model/'
data_train_prefix = prefix + '/train_data/'

# Created once at cold start; DynamoDB connection in get_dynamodb_item.py is also module-level
holiday_service = HolidayService(s3_client, bucket, data_train_prefix)
student_service = StudentService()

def lambda_handler(event, context):
    # event = holiday_service.annotate_event(event)

    df = pd.DataFrame([event])

    calling_data = build_calling_data(df)
    # print("Calling data:", calling_data)
   
    service = DataService()
    query_data = service.calling_to_query(calling_data, holiday_service=holiday_service, student_service=student_service)
    # print("Query data:", query_data)

    event_dict = query_data.X.iloc[0].to_dict()
    # print("Event dict for prediction:", event_dict)

    # Convert event dict to JSON string
    payload = json.dumps(event_dict)

    print("Payload for SageMaker endpoint:", payload)

    # # Invoke the SageMaker endpoint with the payload
    # endpoint_name = ENDPOINT_NAME
    # runtime = boto3.client("sagemaker-runtime")
    
    # try:
    #     # print("ANTES DEL ENDPOINT")

    #     response = runtime.invoke_endpoint(
    #         EndpointName=endpoint_name,
    #         ContentType="application/json",
    #         Body=payload
    #     )

    #     # print("RAW RESPONSE:", response)

    #     result = response["Body"].read().decode("utf-8")
    #     # print("RESULT:", result)

    #     parsed = json.loads(result)
    #     return parsed[0]

    # except Exception as e:
    #     print("ERROR CALLING ENDPOINT:", str(e))
    #     raise e



# Simulated Lambda event (as a dict)
event = {
    'classroomRequestId': 12345,
    'timeZone': 'America/New_York',
    'courseSubTypeId': 4,
    'startTime': '2023-10-01T10:00:00Z',
    'personId': 54321
}

# Simulate Lambda invocation
result = lambda_handler(event, None)

print("Raw result:", result)