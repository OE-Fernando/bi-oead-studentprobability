from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd

from holiday_service_lambda import HolidayService
from student_srv_lambda import StudentService
from time_srv_lambda import compute_time_features
from data_contracts_lambda import (  # type: ignore  # pylint: disable=import-error
    CallingData,
    DataContractError,
    HistoricalData,
    QueryData,
    QUERY_SCHEMA,
    TRAINING_SCHEMA,
    TrainingData,
    build_query_data,
    build_training_data,
)


@dataclass
class DataService:
    """Transforms between validated data-contract objects."""

    def historical_to_training(self, historical_data: HistoricalData) -> TrainingData:
        """Convert HistoricalData into TrainingData by keeping only training features + y."""
        df = historical_data.X.copy()

        # Historical data can contain extra columns (for example isOrientation/isPrivate).
        # Keep only training features before validation.
        common_training_columns = [
            column for column in TRAINING_SCHEMA.feature_columns if column in df.columns
        ]
        df = df[common_training_columns].copy()

        df["dow"] = df["dow"].astype(str)
        df["studLevel"] = df["studLevel"].astype(str)

        df['y'] = historical_data.y

        return build_training_data(df, target_column='y')


    def calling_to_query(
        self,
        calling_data: CallingData,
        holiday_service: HolidayService | None = None,
        student_service: StudentService | None = None,
    ) -> QueryData:
        """Convert CallingData into QueryData with startTime -> holiday flags conversion."""
        df = calling_data.X.copy()

        df['courseSubTypeId'] = df['courseSubTypeId']

        if 'startTime' not in df.columns:
            raise DataContractError("CallingData.X must include 'startTime' to build QueryData.")
        
        if 'timeZone' not in df.columns:
            raise DataContractError("CallingData.X must include 'timeZone' to build QueryData.")
        
        df['dow'] = ''
        df['deltaDays'] = 0
        df['deltaHours'] = 0
        df['hourOfDay'] = 0
        df['minuteOfHour'] = 0
        df['isWeekend'] = 0

        for idx, row in df.iterrows():
            try:
                tf = compute_time_features(row['startTime'], str(row['timeZone']))
            except ValueError as exc:
                raise DataContractError(str(exc)) from exc
            df.at[idx, 'dow']          = tf['dow']
            df.at[idx, 'deltaDays']    = tf['deltaDays']
            df.at[idx, 'deltaHours']   = tf['deltaHours']
            df.at[idx, 'hourOfDay']    = tf['hourOfDay']
            df.at[idx, 'minuteOfHour'] = tf['minuteOfHour']
            df.at[idx, 'isWeekend']    = tf['isWeekend']


        if 'personId' not in df.columns:
            raise DataContractError("CallingData.X must include 'personId' to build QueryData.")

        _svc = student_service if student_service is not None else StudentService()
        student_cols = ['enrollment', 'studentHistory', 'country_iso', 'isb2b', 'gender', 'ageGroup', 'studentLevelNumber']
        for col in student_cols:
            df[col] = ''

        for idx, row in df.iterrows():
            features = _svc.extract_student_features(int(row['personId']))
            for col in student_cols:
                df.at[idx, col] = features.get(col, '')

        if holiday_service is not None:
            # Real holiday conversion using holiday lookup service

            df['isHoliday'] = 0
            df['isHolidayPre'] = 0
            df['isHolidayPost'] = 0
          

            for idx, row in df.iterrows():
                flags = holiday_service.get_holiday_flags(str(row['startTime']), str(row['country_iso']))
                df.at[idx, 'isHoliday'] = flags[0]
                df.at[idx, 'isHolidayPre'] = flags[1]
                df.at[idx, 'isHolidayPost'] = flags[2]
        else:
            # Fallback conversion rule (for tests or legacy behavior)
            dates = pd.to_datetime(df['startTime'], errors='coerce')
            if dates.isna().any():
                raise DataContractError("CallingData.X.startTime must be parseable as a valid date.")

            holiday = ((dates.dt.day % 10) == 0).astype('int64')
            holiday_pre = (((dates + pd.Timedelta(days=1)).dt.day % 10) == 0).astype('int64')
            holiday_post = (((dates - pd.Timedelta(days=1)).dt.day % 10) == 0).astype('int64')

            df['isHoliday'] = holiday
            df['isHolidayPre'] = holiday_pre
            df['isHolidayPost'] = holiday_post

        # Query contract expects categorical columns as string.
        for column in QUERY_SCHEMA.categorical_features:
            if column in df.columns:
                df[column] = df[column].astype('string')

        # Keep only QueryData expected features; validator will enforce missing/typing rules.
        query_columns = [column for column in QUERY_SCHEMA.feature_columns if column in df.columns]
        query_df = df[query_columns].copy()

        return build_query_data(query_df)
