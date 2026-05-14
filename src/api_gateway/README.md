# API Gateway Test Suite

This folder contains testing scripts for the Junior Probability Prediction API Gateway.

## Files

- `test_api_gateway.py` - Main test script for API gateway testing
- `requirements.txt` - Python dependencies for API testing

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Test Run

Run the default test suite (10 randomized requests):

```bash
python test_api_gateway.py
```

### Custom Number of Tests

Modify the `NUM_TESTS` variable in the script or run with custom parameters (future enhancement).

## Test Features

- **10 randomized test requests** with realistic data
- **Future date guarantee** - `book_date` is always 1-7 days in the future
- **Realistic data generation** using predefined lists:
  - Countries: AR, CL, CO, MX, PE, VE, ES
  - Enrollments: s07, s31, sMx
  - Languages: es, en, pt
  - Class types: group, orientation, private
  - Student hour ranges: 2-6, 2-10, 4-6, 4-8, 6-10, 8-10

## Output

The script provides:
- **Detailed logs** for each test request and response
- **Summary report** with:
  - Total/successful/failed request counts
  - Success rate percentage
  - Response value statistics (min/max/average/std dev)
  - API health status (HEALTHY/DEGRADED/UNHEALTHY)
  - Detailed failure logs for troubleshooting

## API Health Indicators

- **✓ HEALTHY**: ≥80% success rate
- **✗ DEGRADED**: 50-79% success rate
- **✗ UNHEALTHY**: <50% success rate

## Example Output

```
================================================================================
API GATEWAY TEST SUITE
================================================================================
Endpoint: https://bi-api.openenglish.com/juniorprob
Number of tests: 10
Date range: 1-7 days in the future
================================================================================

[Test 1] Making request...
  Payload: {
    "dow": 3,
    "ageGroup": 2,
    "studLevel": 5,
    "stuH": "4-8",
    "country_iso": "MX",
    "enrollment": "sMx",
    "deltaDays": -15,
    "deltaHours": -8,
    "hourOfDay": 14,
    "minuteOfHour": 30,
    "isWeekend": 0,
    "native_language": "es",
    "class_type": "group",
    "book_date": "2026-04-01"
  }
  ✓ Success! Response: 0.742156

[... more test results ...]

================================================================================
TEST SUMMARY REPORT
================================================================================
Total requests:     10
Successful:         10 (100.0%)
Failed:             0

Response Value Statistics (from 10 successful tests):
  Min:              0.123456
  Max:              0.987654
  Average:          0.654321
  Std Dev:          0.234567

API Health Status:  ✓ HEALTHY
================================================================================
```

## Manual Single Test

To test a single request manually (equivalent to the curl command):

```bash
curl -X POST "https://bi-api.openenglish.com/juniorprob" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"dow": 3, "ageGroup": 2, "studLevel": 3, "stuH": "2-10", "country_iso": "AR", "enrollment": "s07", "deltaDays": -1, "deltaHours": -16, "hourOfDay": 3, "minuteOfHour": 0, "isWeekend": 0, "native_language": "es", "class_type": "orientation", "book_date": "2026-03-30"}'
```

END OF FILE