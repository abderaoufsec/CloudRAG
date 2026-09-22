targetScope = 'resourceGroup'

param projectName string = 'cloudrag'
param location string = resourceGroup().location
param registryName string
param environmentName string
param pullIdentityName string
param apiImage string
param frontendImage string
param enablePersistentStorage bool = false
param storageAccountName string = ''

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: pullIdentityName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = if (enablePersistentStorage) {
  name: storageAccountName
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' existing = if (enablePersistentStorage) {
  parent: storageAccount
  name: 'default'
}

resource dataShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' existing = if (enablePersistentStorage) {
  parent: fileService
  name: 'cloudrag-data'
}

resource storageLink 'Microsoft.App/managedEnvironments/storages@2024-03-01' = if (enablePersistentStorage) {
  parent: environment
  name: 'cloudrag-data'
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: dataShare.name
      accessMode: 'ReadWrite'
    }
  }
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullIdentity.id, acrPullRoleDefinitionId)
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
    principalId: pullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource api 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${projectName}-api'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  dependsOn: enablePersistentStorage ? [
    acrPull
    storageLink
  ] : [
    acrPull
  ]
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: pullIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: [
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
            {
              name: 'CORS_ORIGINS'
              value: '*'
            }
            {
              name: 'TRUSTED_HOSTS'
              value: '*'
            }
            {
              name: 'LLM_PROVIDER'
              value: 'local'
            }
            {
              name: 'OLLAMA_BASE_URL'
              value: 'http://localhost:11434'
            }
            {
              name: 'OLLAMA_MODEL'
              value: 'qwen3:8b'
            }
            {
              name: 'VECTOR_STORE'
              value: 'faiss'
            }
          ]
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          volumeMounts: enablePersistentStorage ? [
            {
              volumeName: 'cloudrag-data'
              mountPath: '/app/data'
            }
          ] : []
        }
      ]
      scale: {
        minReplicas: enablePersistentStorage ? 1 : 0
        maxReplicas: 1
      }
      volumes: enablePersistentStorage ? [
        {
          name: 'cloudrag-data'
          storageType: 'AzureFile'
          storageName: 'cloudrag-data'
        }
      ] : []
    }
  }
}

resource frontend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${projectName}-web'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  dependsOn: [
    acrPull
  ]
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: pullIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: frontendImage
          env: [
            {
              name: 'VITE_API_URL'
              value: 'https://${api.properties.configuration.ingress.fqdn}'
            }
          ]
          resources: {
            cpu: 0.25
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

output apiUrl string = 'https://${api.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontend.properties.configuration.ingress.fqdn}'
