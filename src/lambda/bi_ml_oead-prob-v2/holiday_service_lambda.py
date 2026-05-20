import datetime
from typing import Any, Dict, Tuple

import pandas as pd


class HolidayService:
    """Holiday features derived from a holiday lookup table in S3."""

    def __init__(self, s3_client: Any, bucket: str, data_train_prefix: str):
        self.s3_client = s3_client
        self.bucket = bucket
        self.data_train_prefix = data_train_prefix

        print(f"Loading holiday lookup table from s3://{bucket}/{data_train_prefix}lk_holiday.csv")

        file = self.s3_client.get_object(Bucket=self.bucket, Key=self.data_train_prefix + 'lk_holiday.csv')
        self.df_holiday = pd.read_csv(file['Body'], sep=',')

        # Normalize date column to string in YYYY-MM-DD for consistent comparisons
        if 'date' in self.df_holiday.columns:
            self.df_holiday['date'] = self.df_holiday['date'].astype(str)
        else:
            raise ValueError("Holiday lookup table must contain 'date' column")

        if 'country_code' not in self.df_holiday.columns:
            raise ValueError("Holiday lookup table must contain 'country_code' column")

    @staticmethod
    def _format_date(date_obj: datetime.date) -> str:
        return date_obj.strftime('%Y-%m-%d')

    def get_holiday_flags(self, date_str: str, country_iso: str) -> Tuple[int, int, int]:
        try:
            start_time = pd.to_datetime(date_str, utc=True)
            book_date = start_time.date()
        except Exception as exc:
            raise ValueError(f"startTime must be parseable as a date/time: {date_str}") from exc
        
        date_keys = {
            'isHoliday': self._format_date(book_date),
            'isHolidayPre': self._format_date(book_date - datetime.timedelta(days=1)),
            'isHolidayPost': self._format_date(book_date + datetime.timedelta(days=1)),
        }

        results = {}
        for key, date_value in date_keys.items():
            found = self.df_holiday.loc[
                (self.df_holiday['date'] == date_value) & (self.df_holiday['country_code'] == country_iso)
            ]
            results[key] = 1 if not found.empty else 0

        return results['isHoliday'], results['isHolidayPre'], results['isHolidayPost']

    @staticmethod
    def normalize_is_weekend(value: Any) -> int:
        if isinstance(value, str):
            value = value.strip().lower()
            if value in {'true', '1', 'yes', 'y'}:
                return 1
            return 0

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (int, float)):
            return 1 if value == 1 else 0

        return 0

    def annotate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event['isHoliday'], event['isHolidayPre'], event['isHolidayPost'] = self.get_holiday_flags(
            event.get('startTime', ''), event.get('country_iso', '')
        )

        event['isWeekend'] = self.normalize_is_weekend(event.get('isWeekend', 0))

        return event
