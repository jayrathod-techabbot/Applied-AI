param location string = resourceGroup().location
param containerAppName string = 'book-recommender-${uniqueString(resourceGroup().id)}'
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param envVars array = []

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${containerAppName}-logs'
  location: location
}

resource environment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${containerAppName}-env'
  location: location
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

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8002
      }
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          env: envVars
          resources: {
            cpu: any('0.5')
            memory: '1.0Gi'
          }
        }
      ]
    }
  }
}

output fqdn string = containerApp.properties.configuration.ingress.fqdn
