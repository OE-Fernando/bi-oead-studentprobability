import os
import boto3
import json
import pandas as pd
import datetime

from data_srv_lambda import DataService
from data_contracts_lambda import build_calling_data
from holiday_service_lambda import HolidayService

runtime = boto3.client('runtime.sagemaker')
s3_client = boto3.client('s3')

ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
bucket = os.environ['BUCKET']

prefix = 'bi_oejr_prob_sm' # use this prefix to store all files
modelprefix = prefix + '/model/'
data_train_prefix = prefix + '/train_data/'

# load preprocess template via reusable service
holiday_service = HolidayService(s3_client, bucket, data_train_prefix)

def lambda_handler(event, context):
    event = holiday_service.annotate_event(event)

    df = pd.DataFrame([event])

    calling_data = build_calling_data(df)
    # print("Calling data:", calling_data)
   
    service = DataService()
    query_data = service.calling_to_query(calling_data, holiday_service=holiday_service)
    # print("Query data:", query_data)

    event_dict = query_data.X.iloc[0].to_dict()
    # print("Event dict for prediction:", event_dict)

    # Convert event dict to JSON string
    payload = json.dumps(event_dict)

    # Invoke the SageMaker endpoint with the payload
    endpoint_name = ENDPOINT_NAME
    runtime = boto3.client("sagemaker-runtime")
    
    try:
        # print("ANTES DEL ENDPOINT")

        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=payload
        )

        # print("RAW RESPONSE:", response)

        result = response["Body"].read().decode("utf-8")
        # print("RESULT:", result)

        parsed = json.loads(result)
        return parsed[0]

    except Exception as e:
        print("ERROR CALLING ENDPOINT:", str(e))
        raise e



# Simulated Lambda event (as a dict)
event = {
    "stuH": "4-8",
    "country_iso": "BR",
    "enrollment": "sMax",
    "native_language": "pt-BR",
    "class_type": "group",
    "dow": 7,
    "studLevel": 1,
    "ageGroup": 2,
    "deltaDays": 0,
    "deltaHours": -1,
    "hourOfDay": 7,
    "minuteOfHour": 0,
    "isWeekend": 1,
    "is_holiday": 1,
    "is_holiday_pre": 0,
    "is_holiday_post": 0,
    "book_date": "2026-03-05"
}


# Simulate Lambda invocation
result = lambda_handler(event, None)

print("Raw result:", result)