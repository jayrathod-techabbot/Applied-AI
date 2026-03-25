param location string = resourceGroup().location
param searchServiceName string = 'search-${uniqueString(resourceGroup().id)}'
param sku string = 'basic'

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  sku: {
    name: sku
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
  }
}

output searchServiceEndpoint string = 'https://${searchServiceName}.search.windows.net'
output searchServiceKey string = listAdminKeys(searchService.id, '2023-11-01').primaryKey
