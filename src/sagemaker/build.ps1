param(
    [string]$AccountId = $(if ($env:AWS_ACCOUNT_ID) { $env:AWS_ACCOUNT_ID } else { throw "AWS_ACCOUNT_ID is required. Set AWS_ACCOUNT_ID or pass -AccountId." }),
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
    [string]$RepositoryName = "sagemaker-xgboost-custom",
    [string]$Tag = "1.7-1"
)

$repositoryUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepositoryName}:${Tag}"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path (Join-Path $scriptDir "..") "..")
$dockerfilePath = Join-Path $scriptDir "Dockerfile"

# Force legacy builder for Docker v2 manifest format
$env:DOCKER_BUILDKIT = "0"

Write-Host "Logging in to SageMaker base image ECR: 683313688378.dkr.ecr.$Region.amazonaws.com"
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "683313688378.dkr.ecr.$Region.amazonaws.com"

Write-Host "Building Docker image: $repositoryUri"
Push-Location "$projectRoot"
try {
    docker build --pull -f "src/sagemaker/Dockerfile" -t "$repositoryUri" .
} finally {
    Pop-Location
}
Write-Host "Built Docker image: $repositoryUri"
