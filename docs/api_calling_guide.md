# API Calling Guide — bi_ml_oead-prob-v2

## Overview

The API receives a minimal set of raw inputs and computes all derived features internally. Callers no longer need to pre-calculate time features or provide student attributes — the Lambda function resolves them automatically.

---

## Endpoint

| Environment | URL |
|---|---|
| Production | `https://bi-api.openenglish.com/oeadprob`  |
| Test (v2)  | `https://bi-api.openenglish.com/oeadprob2` |

Method: `POST`  
Content-Type: `application/json`

---

## Request Parameters

Defined by `CALLING_SCHEMA` in `data_contracts_lambda.py`.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `classroomRequestId` | integer | yes | Unique identifier for the classroom request |
| `courseSubTypeId` | integer | yes | Course sub-type identifier |
| `personId` | integer | yes | Student person identifier |
| `startTime` | string (ISO-8601 UTC) | yes | Scheduled class start time, always in **UTC**. Format: `"YYYY-MM-DDTHH:MM:SSZ"` (the trailing `Z` denotes UTC). Example: `"2026-05-22T14:30:00Z"`. Do **not** pass a local time — the Lambda converts to local time using `timeZone`. |
| `timeZone` | string (IANA) | yes | IANA timezone name representing the student's local time, e.g. `"America/New_York"`, `"America/Mexico_City"`, `"America/Bogota"`. Used to derive `dow`, `hourOfDay`, `minuteOfHour`, `deltaDays`, and `deltaHours`. Full list: [IANA Time Zone Database](https://www.iana.org/time-zones). |

---

## Internally Derived Features

The following features are computed by the Lambda function and do **not** need to be provided by the caller:

| Feature | Source | Notes |
|---|---|---|
| `dow` | `startTime` + `timeZone` | Day of week in local time (1=Mon, 7=Sun) |
| `deltaDays` | `startTime` vs. current time | Days from now to class (negative = future) |
| `deltaHours` | `startTime` vs. current time | Hour-of-day difference (negative = class later today) |
| `hourOfDay` | `startTime` + `timeZone` | Local hour of class (0–23) |
| `minuteOfHour` | `startTime` + `timeZone` | Local minute of class (0–59) |
| `isHoliday` | `startTime` + `country_iso` | 1 if class date is a holiday |
| `isHolidayPre` | `startTime` + `country_iso` | 1 if day before class is a holiday |
| `isHolidayPost` | `startTime` + `country_iso` | 1 if day after class is a holiday |
| `enrollment` | `personId` (student DB) | Student enrollment status |
| `studentHistory` | `personId` (student DB) | Student attendance history |
| `country_iso` | `personId` (student DB) | Student country (ISO code) |
| `isb2b` | `personId` (student DB) | B2B student flag |
| `gender` | `personId` (student DB) | Student gender |
| `ageGroup` | `personId` (student DB) | Student age group |
| `studentLevelNumber` | `personId` (student DB) | Student English level number |

---

## Example Call

```bash
C:\Windows\System32\curl.exe -X POST "https://bi-api.openenglish.com/oeadprob2" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{
    \"classroomRequestId\": 98765,
    \"courseSubTypeId\": 3,
    \"personId\": 1001,
    \"startTime\": \"2026-05-22T14:30:00Z\",
    \"timeZone\": \"America/New_York\"
  }"
```

PowerShell equivalent:

```powershell
$body = @{
    classroomRequestId = 98765
    courseSubTypeId    = 3
    personId           = 1001
    startTime          = "2026-05-22T14:30:00Z"
    timeZone           = "America/New_York"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
  -Uri "https://bi-api.openenglish.com/oeadprob2" `
  -ContentType "application/json" `
  -Body $body
```

---

## Response

Returns a JSON object with the predicted probability (0–1) that the student will attend the class.

```json
0.7058585286140442
```
