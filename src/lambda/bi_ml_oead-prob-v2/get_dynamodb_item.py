import argparse
import json


DYNAMODB_TABLE_NAME = "biba_oead_student_features"
AWS_REGION = "us-east-1"

# --------------------------------------------------------------------------
# DynamoDB connection — created once on first call, reused for all subsequent
# calls (Lambda warm-start behaviour). Import-time creation is intentionally
# avoided so that training scripts can load this module without boto3.
# --------------------------------------------------------------------------

_table = None


def _get_table():
    global _table
    if _table is None:
        import boto3
        _table = boto3.resource("dynamodb", region_name=AWS_REGION).Table(DYNAMODB_TABLE_NAME)
    return _table


def get_item_by_pk(pk_value):
    """
    Fetch a single DynamoDB item by partition key.
    """
    from botocore.exceptions import ClientError

    try:
        response = _get_table().get_item(Key={"PK": pk_value})
    except ClientError as exc:
        raise RuntimeError(
            f"Failed to fetch item from DynamoDB: {exc}"
        ) from exc

    return response.get("Item")


def main():

    parser = argparse.ArgumentParser(
        description="Retrieve DynamoDB record by PK."
    )

    parser.add_argument(
        "pk",
        help="Primary key value"
    )

    args = parser.parse_args()

    item = get_item_by_pk(args.pk)

    if item is None:
        print(f"No item found for PK={args.pk}")
        return

    print(json.dumps(item, indent=2, default=str))


if __name__ == "__main__":
    main()