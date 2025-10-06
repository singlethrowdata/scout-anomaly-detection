import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogBody, DialogFooter } from './Dialog'
import { Button } from './Button'
import { Checkbox } from './Checkbox'
import { Search, Loader2, TrendingUp } from 'lucide-react'
import { cn } from '../lib/utils'

// [R13]: Configuration modal for event selection
// → needs: modal-ui-foundation, event-selection-ui
// → provides: conversion-configuration-ui

interface PropertyEvent {
  event_name: string
  event_count: number
  unique_users: number
  is_likely_conversion: boolean
}

interface PropertyMetadata {
  property_id: string
  dataset_id: string
  events: PropertyEvent[]
  total_events: number
  suggested_conversions: string[]
}

interface ConfigurationModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  propertyId: string
  propertyName: string
  existingConversions?: string[]
  existingDomain?: string
  existingNotes?: string
  onSave: (propertyId: string, config: {
    selectedEvents: string[]
    clientName: string
    domain: string
    notes: string
    datasetId?: string
  }) => void
}

// [R13] Industry options for client categorization
const INDUSTRY_OPTIONS = [
  'Automotive',
  'Education',
  'E-commerce',
  'Healthcare',
  'Home Services',
  'Legal',
  'Manufacturing',
  'Professional Services',
  'Real Estate',
  'Restaurant/Food',
  'Retail',
  'Technology',
  'Travel/Tourism',
  'Other'
]

export function ConfigurationModal({
  open,
  onOpenChange,
  propertyId,
  propertyName,
  existingConversions = [],
  existingDomain = '',
  existingNotes = '',
  onSave
}: ConfigurationModalProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [events, setEvents] = useState<PropertyEvent[]>([])
  const [selectedEvents, setSelectedEvents] = useState<Set<string>>(new Set(existingConversions))
  const [searchQuery, setSearchQuery] = useState('')

  // [R13] Editable fields for configuration
  const [clientName, setClientName] = useState(propertyName)
  const [domain, setDomain] = useState(existingDomain)
  const [notes, setNotes] = useState(existingNotes)

  // [R13] New property mode fields
  const isNewProperty = !propertyId || propertyId === ''
  const [newPropertyId, setNewPropertyId] = useState('')

  // [R13] Industry dropdown instead of notes
  const [industry, setIndustry] = useState(existingNotes || '')

  // Load property metadata when modal opens
  useEffect(() => {
    if (!open) return

    setLoading(true)
    setError(null)

    // [R13] Reset state when modal opens with new property
    setClientName(propertyName)
    setDomain(existingDomain)
    setIndustry(existingNotes)
    setSelectedEvents(new Set(existingConversions))

    // Reset new property fields
    if (isNewProperty) {
      setNewPropertyId('')
      setSelectedEvents(new Set())
      setEvents([]) // No events to show for new property
      setLoading(false)
      return
    }

    if (!propertyId) {
      setLoading(false)
      return
    }

    // Load the metadata file
    fetch('/scout_property_metadata.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load property metadata')
        return res.json()
      })
      .then((allMetadata: Record<string, PropertyMetadata>) => {
        // Find this property's metadata
        const metadata = allMetadata[propertyId]
        if (!metadata) {
          throw new Error(`No metadata found for property ${propertyId}`)
        }

        // [R13] Smart client name and domain extraction
        if (!existingDomain && metadata.dataset_id) {
          const datasetName = metadata.dataset_id.split(':')[1]
          // Extract domain from dataset (e.g., analytics_raycatenalexus -> raycatenalexus.com)
          const domainPart = datasetName.replace('analytics_', '').replace(/_/g, '')
          if (domainPart && domainPart !== propertyId) {
            setDomain(`${domainPart}.com`)
            // Also use domain name (without .com) as client name if not already set
            if (propertyName === propertyId) {
              setClientName(domainPart)
            }
          }
        } else if (existingDomain && propertyName === propertyId) {
          // For configured properties, extract client name from domain
          const domainName = existingDomain.replace(/\.(com|net|org|io)$/i, '')
          setClientName(domainName)
        }

        setEvents(metadata.events || [])

        // [R13] Only pre-select events if property is already configured
        if (existingConversions.length > 0) {
          // Property is configured - load existing selections
          setSelectedEvents(new Set(existingConversions))
        } else {
          // Property is unconfigured - don't pre-select anything (let user choose)
          // Suggestions will still show with green badge but won't be auto-checked
          setSelectedEvents(new Set())
        }

        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading metadata:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [open, propertyId, existingConversions, existingDomain, existingNotes, propertyName, isNewProperty])

  const toggleEvent = (eventName: string) => {
    const newSelected = new Set(selectedEvents)
    if (newSelected.has(eventName)) {
      newSelected.delete(eventName)
    } else {
      newSelected.add(eventName)
    }
    setSelectedEvents(newSelected)
  }

  const handleSave = () => {
    const finalPropertyId = isNewProperty ? newPropertyId : propertyId
    // [R13] Auto-generate dataset ID from property ID
    const autoDatasetId = `st-ga4-data:analytics_${finalPropertyId}`

    onSave(finalPropertyId, {
      selectedEvents: Array.from(selectedEvents),
      clientName,
      domain,
      notes: industry, // Industry stored in notes field
      datasetId: isNewProperty ? autoDatasetId : undefined
    })
    onOpenChange(false)
  }

  // [R13] Validation: require fields for save (dataset ID no longer required)
  const canSave = () => {
    if (isNewProperty) {
      return newPropertyId && clientName && domain && industry
    }
    return selectedEvents.size > 0 && clientName && domain
  }

  // [R13] Filter and sort events: selected first, then suggested, then by count
  const filteredAndSortedEvents = events
    .filter(event => event.event_name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      // Selected events first
      const aSelected = selectedEvents.has(a.event_name)
      const bSelected = selectedEvents.has(b.event_name)
      if (aSelected && !bSelected) return -1
      if (!aSelected && bSelected) return 1

      // Then suggested conversions
      if (a.is_likely_conversion && !b.is_likely_conversion) return -1
      if (!a.is_likely_conversion && b.is_likely_conversion) return 1

      // Then by event count
      return b.event_count - a.event_count
    })

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
    return num.toString()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader onClose={() => onOpenChange(false)}>
          <DialogTitle>Configure Conversion Events</DialogTitle>
          <DialogDescription>
            Configure client information and select conversion events for {propertyName}
          </DialogDescription>
        </DialogHeader>

        <DialogBody>
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-scout-blue" />
              <span className="ml-3 text-gray-600">Loading events...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
              <strong className="font-semibold">Error:</strong> {error}
            </div>
          )}

          {!loading && !error && (
            <>
              {/* [R13] New Property mode: Property ID only (dataset auto-generated) */}
              {isNewProperty && (
                <div className="mb-6 space-y-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-sm font-semibold text-blue-800 mb-2">
                    Create New Property Configuration
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Property ID <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={newPropertyId}
                      onChange={(e) => setNewPropertyId(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-scout-blue focus:border-transparent"
                      placeholder="e.g., 249571600"
                    />
                    {newPropertyId && (
                      <p className="mt-1 text-xs text-gray-500">
                        Dataset ID: <code className="bg-gray-100 px-1 rounded">analytics_{newPropertyId}</code>
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* [R13] Client information fields */}
              <div className="mb-6 space-y-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Client Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-scout-blue focus:border-transparent"
                    placeholder="e.g., Single Throw Marketing"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Domain <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-scout-blue focus:border-transparent"
                    placeholder="e.g., singlethrow.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Industry <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-scout-blue focus:border-transparent"
                  >
                    <option value="">Select industry...</option>
                    {INDUSTRY_OPTIONS.map((ind) => (
                      <option key={ind} value={ind}>
                        {ind}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* [R13] Only show event selection for existing properties */}
              {!isNewProperty && (
                <>
                  {/* Search bar */}
                  <div className="mb-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search events..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-scout-blue focus:border-transparent"
                      />
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="mb-4 flex items-center gap-4 text-sm text-gray-600">
                    <span className="font-medium text-scout-blue">{selectedEvents.size} selected</span>
                    <span>•</span>
                    <span>{filteredAndSortedEvents.length} events shown</span>
                    <span>•</span>
                    <span>{events.filter(e => e.is_likely_conversion).length} suggested</span>
                  </div>

                  {/* Event list */}
                  <div className="border border-gray-200 rounded-lg max-h-96 overflow-y-auto">
                    {filteredAndSortedEvents.length === 0 ? (
                      <div className="p-8 text-center text-gray-500">
                        No events found matching "{searchQuery}"
                      </div>
                    ) : (
                      <div className="divide-y divide-gray-100">
                        {filteredAndSortedEvents.map((event) => (
                          <div
                            key={event.event_name}
                            className={cn(
                              'p-3 transition-colors',
                              selectedEvents.has(event.event_name)
                                ? 'bg-scout-blue/5 hover:bg-scout-blue/10'
                                : 'hover:bg-gray-50'
                            )}
                          >
                            <Checkbox
                              checked={selectedEvents.has(event.event_name)}
                              onChange={() => toggleEvent(event.event_name)}
                              label={
                                <div className="flex items-center gap-2">
                                  <span className="font-mono text-sm">{event.event_name}</span>
                                  {event.is_likely_conversion && (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                      <TrendingUp className="h-3 w-3" />
                                      Suggested
                                    </span>
                                  )}
                                </div>
                              }
                              description={`${formatNumber(event.event_count)} events • ${formatNumber(event.unique_users)} users`}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              {/* [R13] Message for new properties */}
              {isNewProperty && (
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                  <strong>Note:</strong> Conversion events can be configured after the property is created and data is available in BigQuery.
                </div>
              )}
            </>
          )}
        </DialogBody>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            variant="default"
            onClick={handleSave}
            disabled={loading || !canSave()}
          >
            {isNewProperty ? 'Create Property' : 'Save Configuration'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

