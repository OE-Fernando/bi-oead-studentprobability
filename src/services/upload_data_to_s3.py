import sagemaker
from project_paths import PATHS, s3_uri

sess = sagemaker.Session()

bucket = sess.default_bucket()

s3_path = sess.upload_data(
    path="data/testing_data_01.csv",
    bucket=PATHS.bucket_name,
    key_prefix=PATHS.data_prefix,
)