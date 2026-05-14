from pathlib import Path
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


# -----------------------------
# CONFIGURATION
# -----------------------------

BUCKET_NAME = "sagemaker-us-east-1-719805443631"
PREFIX = "fernando_test/model"

LOCAL_FILE_NAME = "model.tar.gz"


# -----------------------------
# RESOLVE LOCAL FILE PATH
# -----------------------------

try:
    base_dir = Path(__file__).resolve().parent
except NameError:
    base_dir = Path.cwd()

local_file_path = base_dir / LOCAL_FILE_NAME

if not local_file_path.exists():
    raise FileNotFoundError(f"File not found: {local_file_path}")


# -----------------------------
# GENERATE S3 OBJECT NAME
# -----------------------------

timestamp = datetime.now().strftime("%Y%m%d_%H%M")

s3_filename = f"model_{timestamp}.tar.gz"

s3_key = f"{PREFIX}/{s3_filename}"

s3_uri = f"s3://{BUCKET_NAME}/{s3_key}"


# -----------------------------
# CREATE S3 CLIENT
# -----------------------------

s3_client = boto3.client("s3")


# -----------------------------
# UPLOAD FILE
# -----------------------------

try:
    s3_client.upload_file(
        Filename=str(local_file_path),
        Bucket=BUCKET_NAME,
        Key=s3_key
    )

    print(f"Upload successful")
    print(f"S3 URI: {s3_uri}")

except FileNotFoundError:
    print("Local file not found")

except NoCredentialsError:
    print("AWS credentials not configured")

except ClientError as e:
    print(f"AWS error: {e}")