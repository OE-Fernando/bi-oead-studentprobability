import io
import sys
from pathlib import Path

import pandas as pd

# add lambda package path so we can import modules from bi_ml_oead-prob-v2
BASEPATH = Path(__file__).resolve().parents[1]
LAMBDA_PATH = BASEPATH / 'lambda' / 'bi_ml_oead-prob-v2'
sys.path.insert(0, str(LAMBDA_PATH))

from holiday_service_lambda import HolidayService
from data_srv_lambda import DataService


class FakeS3Client:
    def __init__(self, csv_text: str):
        self.csv_text = csv_text

    def get_object(self, Bucket: str, Key: str):
        return {'Body': io.StringIO(self.csv_text)}


def test_get_holiday_flags():
    csv = 'date,country_code\n2026-03-04,BR\n2026-03-05,BR\n2026-03-06,BR\n'
    s3_client = FakeS3Client(csv)
    service = HolidayService(s3_client, bucket='any', data_train_prefix='prefix/')

    isHoliday, isHolidayPre, isHolidayPost = service.get_holiday_flags('2026-03-05', 'BR')
    assert isHoliday == 1
    assert isHolidayPre == 1
    assert isHolidayPost == 1

    isHoliday, isHolidayPre, isHolidayPost = service.get_holiday_flags('2026-03-07', 'BR')
    assert isHoliday == 0
    assert isHolidayPre == 0
    assert isHolidayPost == 0


def test_annotate_event():
    csv = 'date,country_code\n2026-03-04,BR\n2026-03-05,BR\n2026-03-06,BR\n'
    s3_client = FakeS3Client(csv)
    service = HolidayService(s3_client, bucket='any', data_train_prefix='prefix/')

    event = {'book_date': '2026-03-05', 'country_iso': 'BR', 'isWeekend': 'true'}
    annotated = service.annotate_event(event)

    assert annotated['isHoliday'] == 1
    assert annotated['isHolidayPre'] == 1
    assert annotated['isHolidayPost'] == 1
    assert annotated['isWeekend'] == 1


def test_data_service_calling_to_query_uses_holiday_service():
    csv = 'date,country_code\n2026-03-04,BR\n2026-03-05,BR\n2026-03-06,BR\n'
    s3_client = FakeS3Client(csv)
    holiday_service = HolidayService(s3_client, bucket='any', data_train_prefix='prefix/')

    df = pd.DataFrame([
        {
            'stuH': '4-8',
            'country_iso': 'BR',
            'enrollment': 'sMax',
            'native_language': 'pt-BR',
            'class_type': 'group',
            'dow': 7,
            'studLevel': 1,
            'ageGroup': 2,
            'deltaDays': 0,
            'deltaHours': -1,
            'hourOfDay': 7,
            'minuteOfHour': 0,
            'isWeekend': 'false',
            'book_date': '2026-03-05',
        }
    ])
    from data_contracts_lambda import build_calling_data

    calling_data = build_calling_data(df)
    data_service = DataService()
    query_data = data_service.calling_to_query(calling_data, holiday_service=holiday_service)

    first = query_data.X.iloc[0]
    assert first['isHoliday'] == 1
    assert first['isHolidayPre'] == 1
    assert first['isHolidayPost'] == 1
