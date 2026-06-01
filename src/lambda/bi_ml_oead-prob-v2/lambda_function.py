import os
import boto3
import json
import pandas as pd
import datetime
from datetime import timezone
from decimal import Decimal

from data_srv_lambda import DataService
from data_contracts_lambda import build_calling_data
from holiday_service_lambda import HolidayService
from student_srv_lambda import StudentService

s3_client = boto3.client('s3')

ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
LOG_TABLE_NAME = os.environ.get('LOG_TABLE_NAME', 'biba_oead_probability_log')
bucket = os.environ['BUCKET']

prefix = 'oead-prob'
modelprefix = prefix + '/model/'
data_train_prefix = prefix + '/train_data/'

# Created once at cold start; DynamoDB connection in get_dynamodb_item.py is also module-level
holiday_service = HolidayService(s3_client, bucket, data_train_prefix)
student_service = StudentService()

_log_table = None


def _get_log_table():
    global _log_table
    if _log_table is None:
        _log_table = boto3.resource("dynamodb", region_name="us-east-1").Table(LOG_TABLE_NAME)
    return _log_table


def _safe_int(value, default=0):
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return default


def _log_prediction(event, query_data, probability, epoch_ms):
    try:
        row = query_data.X.iloc[0]
        caller = str(event.get('caller', 'U'))
        classroom_request_id = _safe_int(event.get('classroomRequestId', 0))
        pk = f"{classroom_request_id}#{epoch_ms}"
        reservation_date = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.00+0000')

        item = {
            'PK':                 pk,
            'GSI1PK':             caller,
            'modifiedAtEpoch':    epoch_ms,
            'classroomRequestId': classroom_request_id,
            'reservationDate':    reservation_date,
            'timezone':           str(event.get('timeZone', 'U')),
            'deltaDays':          _safe_int(row['deltaDays']),
            'deltaHours':         _safe_int(row['deltaHours']),
            'courseSubTypeId':    _safe_int(row['courseSubTypeId']),
            'language':           str(event.get('language', 'U')),
            'startTime':          str(event.get('startTime', '')),
            'dow':                _safe_int(row['dow']),
            'hourOfDay':          _safe_int(row['hourOfDay']),
            'minuteOfHour':       _safe_int(row['minuteOfHour']),
            'isWeekend':          _safe_int(row['isWeekend']),
            'isHoliday':          _safe_int(row['isHoliday']),
            'isHolidayPre':       _safe_int(row['isHolidayPre']),
            'isHolidayPost':      _safe_int(row['isHolidayPost']),
            'personId':           _safe_int(event.get('personId', 0)),
            'studentLevelNumber': _safe_int(row['studentLevelNumber'], default=255),
            'enrollment':         str(row['enrollment']),
            'studentHistory':     str(row['studentHistory']),
            'country':            str(row['country_iso']),
            'isb2b':              str(row['isb2b']),
            'gender':             str(row['gender']),
            'ageGroup':           str(row['ageGroup']),
            'caller':             caller,
            'probability':        Decimal(str(round(float(probability), 6))),
        }

        _get_log_table().put_item(Item=item)
    except Exception as e:
        print("WARNING: Failed to log prediction to DynamoDB:", str(e))


def lambda_handler(event, context):
    epoch_ms = int(datetime.datetime.now(timezone.utc).timestamp() * 1000)

    df = pd.DataFrame([event])

    calling_data = build_calling_data(df)

    service = DataService()
    query_data = service.calling_to_query(calling_data, holiday_service=holiday_service, student_service=student_service)

    event_dict = query_data.X.iloc[0].to_dict()

    payload = json.dumps(event_dict)

    runtime = boto3.client("sagemaker-runtime")

    try:
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=payload
        )

        result = response["Body"].read().decode("utf-8")
        parsed = json.loads(result)
        probability = parsed[0]

        _log_prediction(event, query_data, probability, epoch_ms)

        return probability

    except Exception as e:
        print("ERROR CALLING ENDPOINT:", str(e))
        raise e



# Simulated Lambda event (as a dict)
event = {
    'classroomRequestId': 12345,
    'timeZone': 'America/New_York',
    'courseSubTypeId': 4,
    'language': 'en',
    'startTime': '2023-10-01T10:00:00Z',
    'personId': 978456,
    'caller': 'DEV'
}

# Simulate Lambda invocation
result = lambda_handler(event, None)

print("Raw result:", result)