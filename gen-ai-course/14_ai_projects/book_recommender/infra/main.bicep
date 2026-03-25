targetScope = 'resourceGroup'

param location string = resourceGroup().location
param searchServiceName string = 'search-${uniqueString(resourceGroup().id)}'

module aiSearch 'ai_search.bicep' = {
  name: 'aiSearch'
  params: {
    location: location
    searchServiceName: searchServiceName
  }
}

module containerApp 'container_app.bicep' = {
  name: 'containerApp'
  params: {
    location: location
    envVars: [
      {
        name: 'AZURE_SEARCH_ENDPOINT'
        value: aiSearch.outputs.searchServiceEndpoint
      }
      {
        name: 'AZURE_SEARCH_KEY'
        value: aiSearch.outputs.searchServiceKey
      }
    ]
  }
}

output searchEndpoint string = aiSearch.outputs.searchServiceEndpoint
output appFqdn string = containerApp.outputs.fqdn
