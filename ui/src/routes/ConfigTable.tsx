import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card'
import { Button } from '../components/Button'
import { ConfigurationModal } from '../components/ConfigurationModal'
import { Settings, Target, AlertCircle, CheckCircle, XCircle } from 'lucide-react'
// [R13] Import Cloud Storage utilities
// → needs: cloud-storage-module
import { loadPropertyConfig, savePropertyConfig, PropertyConfig } from '../lib/cloudStorage'

// [R13] Property interface from API
interface Property {
  property_id: string
  dataset_id: string
  client_name?: string | null
  domain?: string | null
  conversion_events?: string | null
  notes?: string | null
  is_configured: boolean
}

export default function ConfigTable() {
  // [R13] Cloud Storage data loading state
  // → provides: gcs-property-data
  const [allProperties, setAllProperties] = useState<PropertyConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // [R13] Fetch properties from Cloud Storage on mount
  // → needs: cloud-storage-module
  // → provides: properties-from-gcs
  useEffect(() => {
    const fetchProperties = async () => {
      try {
        const response = await loadPropertyConfig()

        if (!response.success) {
          throw new Error(response.error || 'Failed to load properties')
        }

        setAllProperties(response.data || [])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load properties from Cloud Storage')
        console.error('Error fetching properties:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchProperties()
  }, [])

  // [R13] Modal state management
  // → provides: modal-control
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedProperty, setSelectedProperty] = useState<{
    id: string
    name: string
    existingConversions: string[]
  } | null>(null)

  // Calculate stats from loaded properties
  const configuredCount = allProperties.filter(p => p.is_configured).length
  const unconfiguredCount = allProperties.filter(p => !p.is_configured).length
  const totalConversions = allProperties
    .filter(p => p.conversion_events)
    .reduce((acc, p) => acc + (p.conversion_events?.split(',').length || 0), 0)

  // [R13] Handle Configure/Edit button clicks
  // → provides: property-selection
  const handleConfigureClick = (property: Property) => {
    setSelectedProperty({
      id: property.property_id,
      name: property.client_name || property.property_id,
      existingConversions: property.conversion_events
        ? property.conversion_events.split(',').map(e => e.trim())
        : []
    })
    setModalOpen(true)
  }

  // [R13] Handle Add New Property button click
  // → provides: new-property-creation
  const handleAddNewProperty = () => {
    setSelectedProperty({
      id: '', // Empty ID signals "new property" mode
      name: 'New Property',
      existingConversions: []
    })
    setModalOpen(true)
  }

  // [R13] Handle save from modal
  // → needs: cloud-storage-module
  // → provides: config-persistence-to-gcs
  const handleSaveConfiguration = async (propertyId: string, config: {
    selectedEvents: string[]
    clientName: string
    domain: string
    notes: string
    datasetId?: string // Optional for new properties
  }) => {
    setSaving(true)

    try {
      // Check if this is a new property (propertyId is empty or not in list)
      const isNewProperty = !propertyId || !allProperties.some(p => p.property_id === propertyId)

      if (isNewProperty) {
        // Create new property
        const newProperty: PropertyConfig = {
          property_id: propertyId,
          dataset_id: config.datasetId || `st-ga4-data:analytics_${propertyId}`,
          client_name: config.clientName,
          domain: config.domain,
          conversion_events: config.selectedEvents.join(', '),
          notes: config.notes,
          is_configured: true
        }

        // Add to local state
        const updatedProperties = [...allProperties, newProperty]
        setAllProperties(updatedProperties)

        // Save to Cloud Storage
        const response = await savePropertyConfig(updatedProperties)

        if (!response.success) {
          throw new Error(response.error || 'Failed to save new property')
        }

        console.log('✅ New property created in Cloud Storage:', { propertyId, config })
      } else {
        // Update existing property
        const updatedProperties = allProperties.map(p =>
          p.property_id === propertyId
            ? {
              ...p,
              client_name: config.clientName,
              domain: config.domain,
              conversion_events: config.selectedEvents.join(', '),
              notes: config.notes,
              is_configured: true
            }
            : p
        )

        setAllProperties(updatedProperties)

        // Save to Cloud Storage
        const response = await savePropertyConfig(updatedProperties)

        if (!response.success) {
          throw new Error(response.error || 'Failed to save configuration')
        }

        console.log('✅ Configuration saved to Cloud Storage:', { propertyId, config })
      }
    } catch (err) {
      console.error('❌ Failed to save configuration:', err)
      setError(err instanceof Error ? err.message : 'Failed to save configuration')

      // Revert local state on error
      const response = await loadPropertyConfig()
      if (response.success && response.data) {
        setAllProperties(response.data)
      }
    } finally {
      setSaving(false)
    }
  }

  // [R13] Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Target className="w-12 h-12 text-scout-blue animate-pulse mx-auto mb-4" />
          <p className="text-scout-gray">Loading properties from Cloud Storage...</p>
        </div>
      </div>
    )
  }

  // [R13] Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-scout-red mx-auto mb-4" />
          <p className="text-scout-dark font-semibold mb-2">Failed to load properties</p>
          <p className="text-scout-gray text-sm">{error}</p>
          <p className="text-scout-gray text-sm mt-2">
            Check Cloud Storage permissions and environment variables
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-10 h-10 text-scout-blue" />
            <div>
              <h2 className="text-2xl font-bold text-scout-dark">BigQuery Property Management</h2>
              <p className="text-scout-gray">Cloud Storage backed configuration • st-ga4-data project</p>
            </div>
          </div>
          <Button variant="default" onClick={handleAddNewProperty}>
            <Target className="mr-2 h-4 w-4" />
            Configure New Property
          </Button>
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total Properties</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-dark">{allProperties.length}</div>
            <p className="text-xs text-muted-foreground">In BigQuery</p>
          </CardContent>
        </Card>

        <Card className="border-scout-green/20">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Configured</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-green">{configuredCount}</div>
            <p className="text-xs text-muted-foreground">Active monitoring</p>
          </CardContent>
        </Card>

        <Card className="border-scout-yellow/20">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Unconfigured</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-yellow">{unconfiguredCount}</div>
            <p className="text-xs text-muted-foreground">Available to configure</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Conversions Tracked</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-scout-blue">{totalConversions}</div>
            <p className="text-xs text-muted-foreground">Across configured clients</p>
          </CardContent>
        </Card>
      </div>

      {/* Configuration table */}
      <Card>
        <CardHeader>
          <CardTitle>All Properties ({allProperties.length})</CardTitle>
          <CardDescription>
            {configuredCount} configured for SCOUT monitoring • {unconfiguredCount} available to configure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-scout-gray/20">
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Status</th>
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Property ID</th>
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Dataset</th>
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Client</th>
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Domain</th>
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Conversions</th>
                  <th className="text-left py-3 px-4 font-semibold text-scout-dark">Notes</th>
                  <th className="text-right py-3 px-4 font-semibold text-scout-dark">Actions</th>
                </tr>
              </thead>
              <tbody>
                {allProperties.map((property) => (
                  <tr
                    key={property.property_id}
                    className={`border-b border-scout-gray/10 transition-colors ${property.is_configured
                      ? 'bg-scout-green/5 hover:bg-scout-green/10'
                      : 'hover:bg-scout-light/50'
                      }`}
                  >
                    <td className="py-4 px-4">
                      {property.is_configured ? (
                        <CheckCircle className="w-5 h-5 text-scout-green" />
                      ) : (
                        <XCircle className="w-5 h-5 text-scout-gray/30" />
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <code className="text-xs bg-scout-light px-2 py-1 rounded font-mono">
                        {property.property_id}
                      </code>
                    </td>
                    <td className="py-4 px-4">
                      <code className="text-xs text-scout-gray font-mono">
                        {property.dataset_id.split(':')[1]}
                      </code>
                    </td>
                    <td className="py-4 px-4">
                      {property.client_name ? (
                        <div className="font-medium text-scout-dark">{property.client_name}</div>
                      ) : (
                        <span className="text-scout-gray text-sm">Not configured</span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {property.domain ? (
                        <a
                          href={`https://${property.domain}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-scout-blue hover:underline"
                        >
                          {property.domain}
                        </a>
                      ) : (
                        <span className="text-scout-gray/50 text-sm">—</span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {property.conversion_events ? (
                        <div className="flex flex-wrap gap-1">
                          {property.conversion_events.split(',').slice(0, 2).map((event, idx) => (
                            <span
                              key={idx}
                              className="text-xs bg-scout-green/10 text-scout-green px-2 py-1 rounded"
                            >
                              {event.trim()}
                            </span>
                          ))}
                          {property.conversion_events.split(',').length > 2 && (
                            <span className="text-xs text-scout-gray px-2 py-1">
                              +{property.conversion_events.split(',').length - 2} more
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-scout-gray/50 text-sm">—</span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {property.notes ? (
                        <span className="text-sm text-scout-gray">{property.notes}</span>
                      ) : (
                        <span className="text-scout-gray/50 text-sm">—</span>
                      )}
                    </td>
                    <td className="py-4 px-4 text-right">
                      {property.is_configured ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleConfigureClick(property)}
                        >
                          Edit
                        </Button>
                      ) : (
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleConfigureClick(property)}
                        >
                          Configure
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Configuration Modal */}
      {selectedProperty && (
        <ConfigurationModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          propertyId={selectedProperty.id}
          propertyName={selectedProperty.name}
          existingConversions={selectedProperty.existingConversions}
          existingDomain={allProperties.find(p => p.property_id === selectedProperty.id)?.domain || ''}
          existingNotes={allProperties.find(p => p.property_id === selectedProperty.id)?.notes || ''}
          onSave={handleSaveConfiguration}
        />
      )}

      {/* Save indicator */}
      {saving && (
        <div className="fixed bottom-4 right-4 bg-scout-blue text-white px-4 py-2 rounded-lg shadow-lg">
          Saving to Cloud Storage...
        </div>
      )}
    </div>
  )
}

