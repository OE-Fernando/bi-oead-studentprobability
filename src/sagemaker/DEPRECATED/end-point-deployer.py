import boto3
import os

from sagemaker import image_uris

from project_paths import PATHS, s3_uri


def deploy_sklearn_endpoint():
    # Initialize SageMaker client
    region_name = os.getenv("AWS_REGION", "us-east-1")
    sagemaker_client = boto3.client("sagemaker", region_name=region_name)

    # Configuration
    model_name = os.getenv("SP_MODEL_NAME", "sklearn-student-probability-model")
    endpoint_config_name = os.getenv("SP_ENDPOINT_CONFIG_NAME", "sklearn-endpoint-config")
    endpoint_name = os.getenv("SP_ENDPOINT_NAME", "sklearn-student-probability-endpoint")
    role_arn = os.getenv("SP_ROLE_ARN", "arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerRole")
    instance_type = os.getenv("SP_INSTANCE_TYPE", "ml.m5.large")

    # Container/image configuration.
    # Set SP_SKLEARN_FRAMEWORK_VERSION to the version used for training (example: 1.2-1).
    sklearn_framework_version = os.getenv("SP_SKLEARN_FRAMEWORK_VERSION", "1.2-1")
    py_version = os.getenv("SP_PY_VERSION", "py3")
    sklearn_image_uri = os.getenv(
        "SP_SKLEARN_IMAGE_URI",
        image_uris.retrieve(
            framework="sklearn",
            region=region_name,
            version=sklearn_framework_version,
            py_version=py_version,
            image_scope="inference",
            instance_type=instance_type,
        ),
    )

    print(f"Region: {region_name}")
    print(f"Using sklearn image: {sklearn_image_uri}")
    print(f"Expected sklearn framework version: {sklearn_framework_version}")

    # Create SageMaker model
    create_model_response = sagemaker_client.create_model(
        ModelName=model_name,
        PrimaryContainer={
            "Image": sklearn_image_uri,
            "ModelDataUrl": s3_uri(PATHS.pipeline_output_key),
            "Environment": {
                "SAGEMAKER_PROGRAM": "inference.py",
            },
        },
        ExecutionRoleArn=role_arn,
    )

    print(f"Model created: {create_model_response['ModelArn']}")

    # Create endpoint configuration
    sagemaker_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[
            {
                "VariantName": "Primary",
                "ModelName": model_name,
                "InitialInstanceCount": 1,
                "InstanceType": instance_type,
            }
        ],
    )

    print(f"Endpoint config created: {endpoint_config_name}")

    # Create endpoint
    endpoint_response = sagemaker_client.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_config_name,
    )

    print(f"Endpoint created: {endpoint_response['EndpointArn']}")
    print("Endpoint status: Creating... (this may take 5-10 minutes)")

    return endpoint_name


if __name__ == "__main__":
    endpoint_name = deploy_sklearn_endpoint()
    print(f"Deployment initiated. Endpoint: {endpoint_name}")
