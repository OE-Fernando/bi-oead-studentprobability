param(
    [string]$AccountId = $(if ($env:AWS_ACCOUNT_ID) { $env:AWS_ACCOUNT_ID } else { throw "AWS_ACCOUNT_ID is required. Set AWS_ACCOUNT_ID or pass -AccountId." }),
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
    [string]$RepositoryName = "sagemaker-xgboost-custom",
    [string]$Tag = "1.7-1"
)

$repositoryUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepositoryName}:${Tag}"

Write-Host "Logging in to ECR: $AccountId.dkr.ecr.$Region.amazonaws.com"
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

Write-Host "Ensuring ECR repository exists: $RepositoryName"
aws ecr describe-repositories --repository-names $RepositoryName --region $Region > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Repository not found, creating: $RepositoryName"
    aws ecr create-repository --repository-name $RepositoryName --region $Region | Out-Null
}

Write-Host "Verifying local Docker image exists: $repositoryUri"
docker image inspect $repositoryUri > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Local Docker image '$repositoryUri' not found. Build the image first with build.ps1."
}

Write-Host "Pushing image to ECR: $repositoryUri"

$maxRetries = 3
$retryCount = 0
$pushSuccess = $false

while ($retryCount -lt $maxRetries -and -not $pushSuccess) {
    $retryCount++
    Write-Host "Push attempt $retryCount of $maxRetries"
    
    docker push $repositoryUri
    if ($LASTEXITCODE -eq 0) {
        $pushSuccess = $true
        Write-Host "Push succeeded"
    } else {
        if ($retryCount -lt $maxRetries) {
            Write-Host "Push failed, waiting 10 seconds before retry..."
            Start-Sleep -Seconds 10
        }
    }
}

if (-not $pushSuccess) {
    throw "Failed to push image after $maxRetries attempts"
}

Write-Host "Custom image URI: $repositoryUri"
