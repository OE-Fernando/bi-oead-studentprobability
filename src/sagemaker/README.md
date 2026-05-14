# Custom SageMaker XGBoost Image

This folder contains artifacts to build a local Docker image that extends the official SageMaker XGBoost inference container.

## What it does

- Uses the official SageMaker XGBoost inference base image.
- Copies `src/model/inference.py` into `/opt/program/`.
- Copies `src/model/requirements.txt` into `/opt/program/`.
- Installs your model runtime dependencies inside the container.
- Sets `SAGEMAKER_PROGRAM` and `SAGEMAKER_SUBMIT_DIRECTORY` so SageMaker uses your custom inference script.

## Build and push

From the repository root:

```powershell
.\src\sagemaker\build_and_push.ps1 -AccountId <AWS_ACCOUNT_ID> -Region <AWS_REGION> -RepositoryName sagemaker-xgboost-custom -Tag 1.7-1
```

If you prefer, you can also build manually:

```powershell
docker build --pull -f src/sagemaker/Dockerfile -t <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sagemaker-xgboost-custom:1.7-1 .
```

Then push with:

```powershell
aws ecr get-login-password --region <REGION> | docker login --username AWS --password-stdin "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com"
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sagemaker-xgboost-custom:1.7-1
```

## Use the custom image in SageMaker

Set the environment variable before running `endpoint_deployer.ipynb`:

```powershell
$env:SP_CUSTOM_XGBOOST_IMAGE_URI = "<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/sagemaker-xgboost-custom:1.7-1"
```

The endpoint deployer notebook will use the custom image if `SP_CUSTOM_XGBOOST_IMAGE_URI` is set.
