from dataclasses import dataclass
from datetime import date, datetime
from typing import Sequence

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_integer_dtype, is_string_dtype


# Per-contract feature definitions. Update these lists as each contract evolves.
TRAINING_CATEGORICAL_FEATURES = [
    'courseSubTypeId',
    'dow',
    'studentLevelNumber',
    'enrollment',
    'studentHistory',
    'country',
    'isb2b',
    'gender',
    'ageGroup',
]

TRAINING_INTEGER_FEATURES = [
    'deltaDays',
    'deltaHours',
    'hourOfDay',
    'minuteOfHour',
    'isHoliday',
    'preHoliday',
    'postHoliday',
]

TRAINING_DATE_FEATURES = []

# Defaulted to training features for now; customize independently as needed.
HISTORICAL_CATEGORICAL_FEATURES = [
    'courseSubTypeId',
    'dow',
    'studentLevelNumber',
    'enrollment',
    'studentHistory',
    'country',
    'isb2b',
    'gender',
    'ageGroup',
]

HISTORICAL_INTEGER_FEATURES = [
    'deltaDays',
    'deltaHours',
    'hourOfDay',
    'minuteOfHour',
    'isHoliday',
    'preHoliday',
    'postHoliday',
]

HISTORICAL_DATE_FEATURES = []


QUERY_CATEGORICAL_FEATURES = TRAINING_CATEGORICAL_FEATURES.copy()
QUERY_INTEGER_FEATURES = TRAINING_INTEGER_FEATURES.copy()
QUERY_DATE_FEATURES = []


CALLING_CATEGORICAL_FEATURES = [
    'timezone',
]

CALLING_INTEGER_FEATURES = [
    'classroomRequestId',
    'courseSubTypeId',
    'personId',
]

CALLING_DATE_FEATURES = [
    'startTime',
]


@dataclass(frozen=True)
class FeatureSchema:
    name: str
    categorical_features: tuple[str, ...]
    integer_features: tuple[str, ...]
    date_features: tuple[str, ...]

    @property
    def feature_columns(self) -> list[str]:
        return list(self.categorical_features + self.integer_features + self.date_features)


TRAINING_SCHEMA = FeatureSchema(
    name='TrainingData',
    categorical_features=tuple(TRAINING_CATEGORICAL_FEATURES),
    integer_features=tuple(TRAINING_INTEGER_FEATURES),
    date_features=tuple(TRAINING_DATE_FEATURES),
)

HISTORICAL_SCHEMA = FeatureSchema(
    name='HistoricalData',
    categorical_features=tuple(HISTORICAL_CATEGORICAL_FEATURES),
    integer_features=tuple(HISTORICAL_INTEGER_FEATURES),
    date_features=tuple(HISTORICAL_DATE_FEATURES),
)

QUERY_SCHEMA = FeatureSchema(
    name='QueryData',
    categorical_features=tuple(QUERY_CATEGORICAL_FEATURES),
    integer_features=tuple(QUERY_INTEGER_FEATURES),
    date_features=tuple(QUERY_DATE_FEATURES),
)

CALLING_SCHEMA = FeatureSchema(
    name='CallingData',
    categorical_features=tuple(CALLING_CATEGORICAL_FEATURES),
    integer_features=tuple(CALLING_INTEGER_FEATURES),
    date_features=tuple(CALLING_DATE_FEATURES),
)


# # Backward compatibility for existing imports
# CATEGORICAL_FEATURES = TRAINING_CATEGORICAL_FEATURES
# INTEGER_FEATURES = TRAINING_INTEGER_FEATURES
# DATE_FEATURES = TRAINING_DATE_FEATURES
# REMAINDER_FEATURES = INTEGER_FEATURES
# FEATURE_COLUMNS = TRAINING_SCHEMA.feature_columns


@dataclass(frozen=True)
class TrainingData:
    X: pd.DataFrame
    y: pd.Series


@dataclass(frozen=True)
class HistoricalData:
    X: pd.DataFrame
    y: pd.Series


@dataclass(frozen=True)
class QueryData:
    X: pd.DataFrame


@dataclass(frozen=True)
class CallingData:
    X: pd.DataFrame


class DataContractError(ValueError):
    """Raised when incoming data does not match an expected schema."""


def _format_columns(columns: Sequence[str]) -> str:
    return ', '.join(columns)


def _is_string_series(series: pd.Series) -> bool:
    if is_string_dtype(series):
        return True
    non_null = series.dropna()
    return bool(non_null.map(lambda value: isinstance(value, str)).all())


import pandas as pd
from datetime import date, datetime
from pandas.api.types import is_datetime64_any_dtype


def _is_date_series(series: pd.Series) -> bool:
    # If already datetime dtype → valid
    if is_datetime64_any_dtype(series):
        return True

    non_null = series.dropna()

    if non_null.empty:
        return True

    # Case 1: Already date-like objects
    if non_null.map(lambda value: isinstance(value, (date, datetime, pd.Timestamp))).all():
        return True

    # Case 2: Try strict string format validation (YYYY-MM-DD)
    try:
        pd.to_datetime(non_null, format="%Y-%m-%d", errors="raise")
        return True
    except (ValueError, TypeError):
        return False


def _validate_X_dtypes(X: pd.DataFrame, schema: FeatureSchema) -> None:
    invalid_categorical = [col for col in schema.categorical_features if not _is_string_series(X[col])]
    invalid_integer = [col for col in schema.integer_features if not is_integer_dtype(X[col])]
    invalid_date = [col for col in schema.date_features if not _is_date_series(X[col])]

    if invalid_categorical:
        raise DataContractError(
            f"{schema.name}.X categorical columns must be string: {_format_columns(invalid_categorical)}"
        )

    if invalid_integer:
        raise DataContractError(
            f"{schema.name}.X integer columns must be integer dtype: {_format_columns(invalid_integer)}"
        )

    if invalid_date:
        raise DataContractError(
            f"{schema.name}.X date columns must be date/datetime dtype: {_format_columns(invalid_date)}"
        )


def validate_X(X: pd.DataFrame, schema: FeatureSchema) -> pd.DataFrame:
    feature_columns = schema.feature_columns
    missing = [column for column in feature_columns if column not in X.columns]
    unexpected = [column for column in X.columns if column not in feature_columns]

    if missing:
        raise DataContractError(
            f"{schema.name}.X is missing required columns: {_format_columns(missing)}"
        )

    if unexpected:
        raise DataContractError(
            f"{schema.name}.X has unexpected columns: {_format_columns(unexpected)}"
        )

    normalized_X = X[feature_columns].copy()
    _validate_X_dtypes(normalized_X, schema)

    return normalized_X


def validate_y(y: pd.Series, contract_name: str = 'Data') -> pd.Series:
    allowed_values = {0, 1, False, True}
    invalid_values = sorted(value for value in set(y.dropna().tolist()) if value not in allowed_values)

    if invalid_values:
        raise DataContractError(
            f"{contract_name}.y must be binary (0/1 or False/True). Invalid values: {invalid_values}"
        )

    if y.isna().any():
        raise DataContractError(f"{contract_name}.y must not contain null values.")

    return y.astype(int)


def _build_xy_data(df: pd.DataFrame, schema: FeatureSchema, target_column: str) -> tuple[pd.DataFrame, pd.Series]:
    if target_column not in df.columns:
        raise DataContractError(
            f"Target column '{target_column}' was not found for {schema.name}."
        )

    feature_df = df.drop(columns=[target_column])
    X = validate_X(feature_df, schema)
    y = validate_y(df[target_column], contract_name=schema.name)

    return X, y


def _build_x_data(df: pd.DataFrame, schema: FeatureSchema) -> pd.DataFrame:
    return validate_X(df, schema)


def build_training_data(df: pd.DataFrame, target_column: str = 'y') -> TrainingData:
    X, y = _build_xy_data(df, TRAINING_SCHEMA, target_column)
    return TrainingData(X=X, y=y)


def build_historical_data(df: pd.DataFrame, target_column: str = 'y') -> HistoricalData:
    X, y = _build_xy_data(df, HISTORICAL_SCHEMA, target_column)
    return HistoricalData(X=X, y=y)


def build_query_data(df: pd.DataFrame) -> QueryData:
    X = _build_x_data(df, QUERY_SCHEMA)
    return QueryData(X=X)


def build_calling_data(df: pd.DataFrame) -> CallingData:
    X = _build_x_data(df, CALLING_SCHEMA)
    return CallingData(X=X)
