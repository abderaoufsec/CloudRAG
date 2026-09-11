targetScope = 'resourceGroup'

@description('Short lowercase prefix used in Azure resource names.')
param projectName string = 'cloudrag'

param location string = resourceGroup().location

@description('Creates Azure Files storage for the current SQLite and FAISS files. This can incur storage charges.')
param enablePersistentStorage bool = false

param storageAccountName string = toLower('${projectName}${uniqueString(resourceGroup().id)}')

var environmentName = '${projectName}-env'
var registryName = toLower('${projectName}${uniqueString(subscription().id, resourceGroup().id)}')
var identityName = '${projectName}-pull'

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'none'
    }
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = if (enablePersistentStorage) {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' = if (enablePersistentStorage) {
  parent: storageAccount
  name: 'default'
}

resource dataShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' = if (enablePersistentStorage) {
  parent: fileService
  name: 'cloudrag-data'
}

output registryName string = registry.name
output environmentName string = environment.name
output pullIdentityName string = pullIdentity.name
output storageAccountName string = enablePersistentStorage ? storageAccount.name : ''
