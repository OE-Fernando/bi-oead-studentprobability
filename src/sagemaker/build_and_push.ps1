param(
    [string]$AccountId = $(if ($env:AWS_ACCOUNT_ID) { $env:AWS_ACCOUNT_ID } else { throw "AWS_ACCOUNT_ID is required. Set AWS_ACCOUNT_ID or pass -AccountId." }),
    [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
    [string]$RepositoryName = "sagemaker-xgboost-custom",
    [string]$Tag = "1.7-1"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildScript = Join-Path $scriptDir "build.ps1"
$pushScript = Join-Path $scriptDir "push.ps1"

Write-Host "Running build step..."
& "$buildScript" -AccountId $AccountId -Region $Region -RepositoryName $RepositoryName -Tag $Tag

Write-Host "Running push step..."
& "$pushScript" -AccountId $AccountId -Region $Region -RepositoryName $RepositoryName -Tag $Tag
