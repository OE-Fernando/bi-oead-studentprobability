import json
import pandas as pd
from io import StringIO

# ---- COPY your real input_fn here ----
def input_fn(request_body, request_content_type):
    if request_content_type == "application/json":

        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")

        data = json.loads(request_body)
        df = pd.DataFrame([data])
        return df

    elif request_content_type == "text/csv":

        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")

        return pd.read_csv(StringIO(request_body))

    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")
# ----------------------------------------


# ---- Simulate your JSON payload ----
payload_dict = {
    "dow": "7",
    "studLevel": "6",
    "stuH": "4-8",
    "country_iso": "BR",
    "enrollment": "sMax",
    "native_language": "pt-BR",
    "class_type": "group",
    "ageGroup": 2,
    "deltaDays": 0,
    "deltaHours": -1,
    "hourOfDay": 7,
    "minuteOfHour": 0,
    "isWeekend": 1,
    "isHoliday": 0,
    "isHolidayPre": 0,
    "isHolidayPost": 0
}

payload_json = json.dumps(payload_dict)

# ---- Call input_fn like SageMaker does ----
result = input_fn(payload_json, "application/json")

# ---- Debug output ----
print("TYPE:", type(result))
print("SHAPE:", result.shape)
print("\nCOLUMNS:", list(result.columns))
print("\nDATAFRAME:")
print(result)