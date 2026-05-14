from sagemaker.xgboost.estimator import XGBoost
from sagemaker import get_execution_role
from project_paths import PATHS, s3_uri

role = get_execution_role()
# role = 'arn:aws:iam::719805443631:role/bi_sagemaker'
print(f"Using role: {role}")

estimator = XGBoost(
    entry_point="train.py",
    role=role,
    instance_count=1,
    instance_type="ml.m5.large",
    framework_version="1.7-1",
)

estimator.fit({
    "train": s3_uri(PATHS.test_training_data_key)
})