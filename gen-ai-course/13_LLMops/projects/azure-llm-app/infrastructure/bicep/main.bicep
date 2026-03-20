// ============================================================
// Azure LLM App — Main Bicep Template
// Deploys: Azure OpenAI, Container Apps, Redis, Key Vault,
//          Container Registry, App Insights, Log Analytics
// ============================================================
targetScope = 'resourceGroup'

@description('Environment name: dev, staging, prod')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Application name prefix')
param appName string = 'llmapp'

@description('Container image tag to deploy')
param imageTag string = 'latest'

@description('Azure OpenAI GPT-4o model deployment name')
param openaiDeploymentName string = 'gpt-4o'

var prefix = '${appName}-${environment}'
var tags = {
  environment: environment
  application: appName
  managedBy: 'bicep'
}

// ── Log Analytics Workspace ──────────────────────────────────────────────────
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${prefix}-logs'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

// ── Application Insights ─────────────────────────────────────────────────────
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${prefix}-ai'
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
  }
}

// ── Azure Container Registry ─────────────────────────────────────────────────
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: '${replace(prefix, '-', '')}acr'
  location: location
  tags: tags
  sku: { name: environment == 'prod' ? 'Premium' : 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}

// ── Key Vault ────────────────────────────────────────────────────────────────
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: '${prefix}-kv'
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    networkAcls: {
      defaultAction: environment == 'prod' ? 'Deny' : 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// ── Azure OpenAI ─────────────────────────────────────────────────────────────
resource openai 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: '${prefix}-oai'
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: { name: 'S0' }
  properties: {
    customSubDomainName: '${prefix}-oai'
    publicNetworkAccess: 'Enabled'
  }
}

resource openaiDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openai
  name: openaiDeploymentName
  sku: { name: 'Standard', capacity: 10 }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o'
      version: '2024-05-13'
    }
    versionUpgradeOption: 'OnceCurrentVersionExpired'
    raiPolicyName: 'Microsoft.Default'
  }
}

// ── Redis Cache ──────────────────────────────────────────────────────────────
resource redis 'Microsoft.Cache/redis@2023-04-01' = {
  name: '${prefix}-redis'
  location: location
  tags: tags
  properties: {
    sku: {
      name: environment == 'prod' ? 'Standard' : 'Basic'
      family: 'C'
      capacity: environment == 'prod' ? 1 : 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

// ── Container Apps Environment ───────────────────────────────────────────────
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${prefix}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// ── Container App — User-Assigned Managed Identity ───────────────────────────
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-id'
  location: location
  tags: tags
}

// Grant identity access to Key Vault secrets
resource kvSecretsRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVault.id, managedIdentity.id, 'KeyVaultSecretsUser')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Grant identity pull access to ACR
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, managedIdentity.id, 'AcrPull')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Container App ─────────────────────────────────────────────────────────────
resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: '${prefix}-app'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${managedIdentity.id}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        traffic: [{ latestRevision: true, weight: 100 }]
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: managedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'appinsights-connection-string'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'redis-url'
          value: 'rediss://:${redis.listKeys().primaryKey}@${redis.properties.hostName}:6380'
        }
      ]
    }
    template: {
      revisionSuffix: imageTag
      scale: {
        minReplicas: environment == 'prod' ? 2 : 1
        maxReplicas: environment == 'prod' ? 10 : 3
        rules: [
          {
            name: 'http-scaling'
            http: { metadata: { concurrentRequests: '20' } }
          }
        ]
      }
      containers: [
        {
          name: 'llm-app'
          image: '${acr.properties.loginServer}/llm-app:${imageTag}'
          resources: {
            cpu: environment == 'prod' ? '1.0' : '0.5'
            memory: environment == 'prod' ? '2Gi' : '1Gi'
          }
          env: [
            { name: 'ENVIRONMENT', value: environment }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openai.properties.endpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT', value: openaiDeploymentName }
            { name: 'AZURE_KEY_VAULT_URL', value: keyVault.properties.vaultUri }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', secretRef: 'appinsights-connection-string' }
            { name: 'REDIS_URL', secretRef: 'redis-url' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 15
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health', port: 8000 }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ]
        }
      ]
    }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
output acrLoginServer string = acr.properties.loginServer
output openaiEndpoint string = openai.properties.endpoint
output keyVaultUri string = keyVault.properties.vaultUri
output appInsightsConnectionString string = appInsights.properties.ConnectionString
