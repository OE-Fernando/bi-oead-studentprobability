from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import pandas as pd

from holiday_service_lambda import HolidayService
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


    def calling_to_query(self, calling_data: CallingData, holiday_service: HolidayService | None = None) -> QueryData:
        """Convert CallingData into QueryData with startTime -> holiday flags conversion."""
        df = calling_data.X.copy()

        df['courseSubTypeId'] = df['courseSubTypeId']

        if 'startTime' not in df.columns:
            raise DataContractError("CallingData.X must include 'startTime' to build QueryData.")
        
        if 'timeZone' not in df.columns:
            raise DataContractError("CallingData.X must include 'timeZone' to build QueryData.")
        
    # With row['startTime'] and the current datetime, we could compute
    #   dow: 
    #   deltaDays:
    #   deltaHours:
    #   hourOfDay:
    #   minuteOfHour:
        df['dow'] = ''
        df['deltaDays'] = 0
        df['deltaHours'] = 0
        df['hourOfDay'] = 0
        df['minuteOfHour'] = 0


        if 'personId' not in df.columns:
            raise DataContractError("CallingData.X must include 'personId' to build QueryData.")
        
    # The following columns are extracted from the df['personId'] with the function extract_student_features.
    #   The function {...} = extract_student_features(personId) will return a json with all the extracted features.

        df['enrollment'] = ''
        df['studentHistory'] = ''
        df['country_iso'] = ''
        df['isb2b'] = ''
        df['gender'] = ''
        df['ageGroup'] = ''
        df['studentLevelNumber'] = ''

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
