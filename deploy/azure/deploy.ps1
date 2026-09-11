DEPLOY[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9-]{3,20}$')]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [string]$Location,

    [switch]$EnablePersistentStorage
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI is required. Install it, then run this script again.'
}

Write-Host 'This deployment creates Azure Container Registry and Azure Container Apps.' -ForegroundColor Yellow
Write-Host 'Azure Container Registry can incur charges. Azure Files is created only with -EnablePersistentStorage.' -ForegroundColor Yellow
$confirmation = Read-Host "Type DEPLOY to create resources in $Location"
if ($confirmation -cne 'DEPLOY') {
    Write-Host 'Cancelled. No Azure resources were created.'
    exit 0
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$resourceGroup = "$ProjectName-rg"
$tag = (Get-Date -Format 'yyyyMMddHHmmss')

az login | Out-Null
az provider register --namespace Microsoft.App --wait | Out-Null
az provider register --namespace Microsoft.ContainerRegistry --wait | Out-Null
az provider register --namespace Microsoft.ManagedIdentity --wait | Out-Null
if ($EnablePersistentStorage) {
    az provider register --namespace Microsoft.Storage --wait | Out-Null
}

az group create --name $resourceGroup --location $Location | Out-Null

az deployment group create `
    --name cloudrag-infrastructure `
    --resource-group $resourceGroup `
    --template-file (Join-Path $PSScriptRoot 'infrastructure.bicep') `
    --parameters projectName=$ProjectName enablePersistentStorage=$EnablePersistentStorage.IsPresent | Out-Null

$outputs = az deployment group show `
    --resource-group $resourceGroup `
    --name cloudrag-infrastructure `
    --query properties.outputs `
    --output json | ConvertFrom-Json

$registryName = $outputs.registryName.value
$environmentName = $outputs.environmentName.value
$pullIdentityName = $outputs.pullIdentityName.value
$storageAccountName = $outputs.storageAccountName.value

Push-Location $repoRoot
try {
    az acr build --registry $registryName --image "cloudrag-api:$tag" --file deploy/docker/backend.Dockerfile .
    az acr build --registry $registryName --image "cloudrag-web:$tag" --file deploy/docker/frontend.Dockerfile .
}
finally {
    Pop-Location
}

$registryServer = "$registryName.azurecr.io"
az deployment group create `
    --name cloudrag-apps `
    --resource-group $resourceGroup `
    --template-file (Join-Path $PSScriptRoot 'apps.bicep') `
    --parameters `
        projectName=$ProjectName `
        registryName=$registryName `
        environmentName=$environmentName `
        pullIdentityName=$pullIdentityName `
        apiImage="$registryServer/cloudrag-api:$tag" `
        frontendImage="$registryServer/cloudrag-web:$tag" `
        enablePersistentStorage=$EnablePersistentStorage.IsPresent `
        storageAccountName=$storageAccountName

Write-Host "\nDeployment complete. Open the frontend URL in the output above." -ForegroundColor Green
Write-Host "To remove every deployed resource: az group delete --name $resourceGroup --yes --no-wait" -ForegroundColor Yellow
