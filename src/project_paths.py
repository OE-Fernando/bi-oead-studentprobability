import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectPaths:
    bucket_name: str = os.getenv("SP_S3_BUCKET", "sagemaker-us-east-1-719805443631")
    training_data_key: str = os.getenv("SP_TRAINING_DATA_KEY", "fernando_test/data/students_prob_show_up_to_lc_data.csv")
    # pipeline_output_key: str = os.getenv("SP_PIPELINE_OUTPUT_KEY", "fernando_test/models/xgboost_pipeline.pkl")
    pipeline_output_key: str = os.getenv("SP_PIPELINE_OUTPUT_KEY", "fernando_test/models/model.tar.gz")
    code_prefix: str = os.getenv("SP_CODE_PREFIX", "fernando_test/code/")
    model_prefix: str = os.getenv("SP_MODEL_PREFIX", "fernando_test/models/")
    temp_prefix: str = os.getenv("SP_TEMP_PREFIX", "fernando_test/temp/")

    # training_test_data_key: str = os.getenv("SP_TRAINING_TEST_DATA_KEY", "testing/train/testing_data_01.csv")
    data_prefix: str = os.getenv("SP_DATA_KEY", "fernando_test/data/train")
    test_training_data_key: str = os.getenv("SP_TEST_TRAINING_DATA_KEY", "fernando_test/data/train/testing_data_01.csv")


PATHS = ProjectPaths()


def s3_uri(key: str) -> str:
    return f"s3://{PATHS.bucket_name}/{key}"
