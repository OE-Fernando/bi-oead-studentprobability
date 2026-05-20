#!/usr/bin/env python
"""
API Gateway Test Script

Tests the junior probability prediction API gateway with multiple randomized requests.
Each request uses realistic randomized data with startTime guaranteed to be in the future (1-7 days ahead).
"""

import requests
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics


# Configuration
API_ENDPOINT = "https://bi-api.openenglish.com/juniorprob2"
NUM_TESTS = 10
DATE_RANGE_DAYS = (1, 7)  # startTime will be 1-7 days from today

# Realistic predefined values for each field
COUNTRIES = ["AR", "CL", "CO", "MX", "PE", "VE", "ES"]
ENROLLMENTS = ["s07", "s31", "sMx"]
LANGUAGES = ["es", "en", "pt"]
CLASS_TYPES = ["group", "orientation", "private"]
STU_H_VALUES = ["2-6", "2-10", "4-6", "4-8", "6-10", "8-10"]

# Realistic ranges for numeric values
DOW_RANGE = (1, 7)  # Day of week (1-7)
AGE_GROUP_RANGE = (1, 5)  # Age group categories
STUD_LEVEL_RANGE = (1, 8)  # Student level
DELTA_DAYS_RANGE = (-30, 0)  # Days before class
DELTA_HOURS_RANGE = (-48, -1)  # Hours before class
HOUR_OF_DAY_RANGE = (0, 23)  # Hour of day
MINUTE_OF_HOUR_RANGE = (0, 59)  # Minute


def generate_random_payload() -> Dict:
    """Generate a random payload with realistic values."""
    # Generate a future date (1-7 days from today)
    days_ahead = random.randint(DATE_RANGE_DAYS[0], DATE_RANGE_DAYS[1])
    future_date = datetime.now() + timedelta(days=days_ahead)
    startTime = future_date.strftime("%Y-%m-%d")

    payload = {
        "dow": random.randint(DOW_RANGE[0], DOW_RANGE[1]),
        "ageGroup": random.randint(AGE_GROUP_RANGE[0], AGE_GROUP_RANGE[1]),
        "studLevel": random.randint(STUD_LEVEL_RANGE[0], STUD_LEVEL_RANGE[1]),
        "stuH": random.choice(STU_H_VALUES),
        "country_iso": random.choice(COUNTRIES),
        "enrollment": random.choice(ENROLLMENTS),
        "deltaDays": random.randint(DELTA_DAYS_RANGE[0], DELTA_DAYS_RANGE[1]),
        "deltaHours": random.randint(DELTA_HOURS_RANGE[0], DELTA_HOURS_RANGE[1]),
        "hourOfDay": random.randint(HOUR_OF_DAY_RANGE[0], HOUR_OF_DAY_RANGE[1]),
        "minuteOfHour": random.randint(MINUTE_OF_HOUR_RANGE[0], MINUTE_OF_HOUR_RANGE[1]),
        "isWeekend": random.randint(0, 1),
        "native_language": random.choice(LANGUAGES),
        "class_type": random.choice(CLASS_TYPES),
        "startTime": startTime,
    }
    return payload


def make_api_request(payload: Dict, test_num: int) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Make a single API request and return (success, response_value, error_message).

    Args:
        payload: Request payload
        test_num: Test number for logging

    Returns:
        Tuple of (success, response_value, error_message)
    """
    try:
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        print(f"\n[Test {test_num}] Making request...")
        print(f"  Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=10
        )

        # Check if request was successful
        if response.status_code == 200:
            try:
                result = float(response.text.strip())
                print(f"  ✓ Success! Response: {result}")
                return True, result, None
            except ValueError:
                error_msg = f"Response is not a float: {response.text}"
                print(f"  ✗ Error: {error_msg}")
                return False, None, error_msg
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"  ✗ Error: {error_msg}")
            return False, None, error_msg

    except requests.exceptions.Timeout:
        error_msg = "Request timeout (10s exceeded)"
        print(f"  ✗ Error: {error_msg}")
        return False, None, error_msg
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"  ✗ Error: {error_msg}")
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"  ✗ Error: {error_msg}")
        return False, None, error_msg


def run_tests(num_tests: int = NUM_TESTS) -> None:
    """Run the API gateway test suite."""
    print("=" * 80)
    print("API GATEWAY TEST SUITE")
    print("=" * 80)
    print(f"Endpoint: {API_ENDPOINT}")
    print(f"Number of tests: {num_tests}")
    print(f"Date range: {DATE_RANGE_DAYS[0]}-{DATE_RANGE_DAYS[1]} days in the future")
    print("=" * 80)

    results: List[Tuple[bool, float]] = []
    failed_tests: List[Dict] = []

    for i in range(1, num_tests + 1):
        # Generate random payload
        payload = generate_random_payload()

        # Make request
        success, response_value, error_msg = make_api_request(payload, i)

        if success:
            results.append((True, response_value))
        else:
            results.append((False, None))
            failed_tests.append({
                "test_num": i,
                "payload": payload,
                "error": error_msg
            })

    # Generate summary report
    print("\n" + "=" * 80)
    print("TEST SUMMARY REPORT")
    print("=" * 80)

    total_tests = len(results)
    successful_tests = sum(1 for success, _ in results if success)
    failed_tests_count = total_tests - successful_tests
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"Total requests:     {total_tests}")
    print(f"Successful:         {successful_tests} ({success_rate:.1f}%)")
    print(f"Failed:             {failed_tests_count}")

    # Calculate statistics for successful responses
    successful_responses = [value for success, value in results if success and value is not None]
    if successful_responses:
        print(f"\nResponse Value Statistics (from {len(successful_responses)} successful tests):")
        print(f"  Min:              {min(successful_responses):.6f}")
        print(f"  Max:              {max(successful_responses):.6f}")
        print(f"  Average:          {statistics.mean(successful_responses):.6f}")
        if len(successful_responses) > 1:
            print(f"  Std Dev:          {statistics.stdev(successful_responses):.6f}")

    # Report on API health
    print(f"\nAPI Health Status:  {'✓ HEALTHY' if success_rate >= 80 else '✗ DEGRADED' if success_rate >= 50 else '✗ UNHEALTHY'}")

    # Report failed tests if any
    if failed_tests_count > 0:
        print(f"\n" + "-" * 80)
        print("FAILED TEST DETAILS")
        print("-" * 80)
        for failed in failed_tests:
            print(f"\nTest {failed['test_num']}:")
            print(f"  Payload:  {json.dumps(failed['payload'], indent=4)}")
            print(f"  Error:    {failed['error']}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_tests()