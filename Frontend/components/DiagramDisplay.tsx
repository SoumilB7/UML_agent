'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import mermaid from 'mermaid'
import { trackMermaidCopy, trackVariationSelection, trackVariationHover, trackImageCopy, trackZoomToggle, trackPanToggle } from '@/utils/rlTracking'
import FeedbackPanel from './FeedbackPanel'

interface DiagramDisplayProps {
  mermaidCode: string
  isLoading: boolean
  variations?: string[]
  selectedVariationIndex?: number | null
  onSelectVariation?: (index: number) => void
  onConfirmSelection?: () => void
  diagramId?: string
}

interface VariationThumbnailProps {
  mermaidCode: string
  index: number
  isSelected: boolean
  onSelect: () => void
  diagramId?: string
}

function VariationThumbnail({ mermaidCode, index, isSelected, onSelect, diagramId }: VariationThumbnailProps & { diagramId?: string }) {
  const [thumbnailUrl, setThumbnailUrl] = useState<string>('')
  const [isRendering, setIsRendering] = useState(false)
  const [renderError, setRenderError] = useState(false)

  useEffect(() => {
    if (!mermaidCode) {
      setThumbnailUrl('')
      setIsRendering(false)
      setRenderError(false)
      return
    }

    const renderThumbnail = async () => {
      setIsRendering(true)
      setRenderError(false)
      let tempContainer: HTMLDivElement | null = null
      
      try {
        // Ensure mermaid is initialized
        if (typeof mermaid === 'undefined' || !mermaid.run) {
          throw new Error('Mermaid is not initialized')
        }

        // Add a delay based on index to avoid simultaneous rendering conflicts
        // This helps prevent race conditions when multiple thumbnails render at once
        await new Promise(resolve => setTimeout(resolve, index * 300))

        // Generate a truly unique ID for this render
        const uniqueId = `variation-thumb-${index}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

        // Create a unique container for this thumbnail
        tempContainer = document.createElement('div')
        tempContainer.style.position = 'absolute'
        tempContainer.style.left = '-9999px'
        tempContainer.style.top = '-9999px'
        tempContainer.style.width = '200px'
        tempContainer.style.height = '200px'
        tempContainer.style.visibility = 'hidden'
        document.body.appendChild(tempContainer)

        // Create the mermaid div with unique ID
        const div = document.createElement('div')
        div.className = 'mermaid'
        div.id = uniqueId
        div.textContent = mermaidCode.trim()
        tempContainer.appendChild(div)

        // Wait a bit to ensure DOM is ready
        await new Promise(resolve => setTimeout(resolve, 150))

        // Render with mermaid - use suppressErrors: true to avoid breaking other renders
        await mermaid.run({
          nodes: [div],
          suppressErrors: true,
        })

        // Wait and retry to find SVG (mermaid might need more time)
        let svgElement: SVGElement | null = null
        for (let retry = 0; retry < 5; retry++) {
          await new Promise(resolve => setTimeout(resolve, 200))
          svgElement = div.querySelector('svg')
          if (svgElement) break
        }

        if (svgElement) {
          const svgData = new XMLSerializer().serializeToString(svgElement)
          const svgDataUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
          setThumbnailUrl(svgDataUrl)
          setRenderError(false)
        } else {
          console.warn(`No SVG found for variation ${index + 1} after rendering. Mermaid code length: ${mermaidCode.length}`)
          // Log the mermaid code for debugging
          console.debug(`Mermaid code for variation ${index + 1}:`, mermaidCode.substring(0, 200))
          setRenderError(true)
        }

      } catch (error) {
        console.error(`Error rendering thumbnail for variation ${index + 1}:`, error)
        setRenderError(true)
        setThumbnailUrl('')
      } finally {
        setIsRendering(false)
        // Cleanup after a delay
        setTimeout(() => {
          if (tempContainer && document.body.contains(tempContainer)) {
            document.body.removeChild(tempContainer)
          }
        }, 3000)
      }
    }

    renderThumbnail()
  }, [mermaidCode, index])

  return (
    <button
      onClick={onSelect}
      className={`relative p-2 border-2 rounded-lg transition-all ${
        isSelected
          ? 'border-primary-600 bg-primary-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50/50'
      }`}
    >
      <div className="aspect-square w-full bg-gray-50 rounded overflow-hidden flex items-center justify-center">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={`Variation ${index + 1}`}
            className="w-full h-full object-contain"
            onError={() => {
              console.error(`Failed to load thumbnail for variation ${index + 1}`)
              setRenderError(true)
            }}
          />
        ) : renderError ? (
          <div className="text-xs text-red-400 text-center p-2">
            Render Error
          </div>
        ) : (
          <div className="text-xs text-gray-400">
            {isRendering ? 'Rendering...' : 'Loading...'}
          </div>
        )}
      </div>
      <div className="mt-2 text-center">
        <span className={`text-xs font-medium ${isSelected ? 'text-primary-700' : 'text-gray-600'}`}>
          Variation {index + 1}
        </span>
      </div>
      {isSelected && (
        <div className="absolute top-1 right-1 bg-primary-600 rounded-full p-1">
          <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>
      )}
    </button>
  )
}

export default function DiagramDisplay({ 
  mermaidCode, 
  isLoading,
  variations = [],
  selectedVariationIndex = null,
  onSelectVariation,
  onConfirmSelection,
  diagramId
}: DiagramDisplayProps) {
  const svgRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const [imageUrl, setImageUrl] = useState<string>('')
  const [renderError, setRenderError] = useState<string>('')
  // Use diagramId from props, or generate a fallback if not provided
  const effectiveDiagramId = diagramId || `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  
  // Zoom and pan state
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [copied, setCopied] = useState(false)
  const [zoomEnabled, setZoomEnabled] = useState(true)
  const [panEnabled, setPanEnabled] = useState(true)
  const zoomTrackTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  // Track if zoom/pan have been recorded for the current diagram
  const zoomRecordedRef = useRef<string | null>(null)
  const panRecordedRef = useRef<string | null>(null)

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      themeVariables: {
        primaryColor: '#667eea',
        primaryTextColor: '#1f2937',
        primaryBorderColor: '#667eea',
        lineColor: '#374151',
        secondaryColor: '#818cf8',
        tertiaryColor: '#f3f4f6',
        background: '#ffffff',
        mainBkgColor: '#ffffff',
        secondBkgColor: '#f9fafb',
        textColor: '#1f2937',
      },
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
      },
    })
  }, [])

  useEffect(() => {
    if (!mermaidCode || !svgRef.current) {
      setImageUrl('')
      setRenderError('')
      return
    }

    const renderDiagram = async () => {
      try {
        setRenderError('')
        setImageUrl('')

        // Create a temporary container for rendering
        const tempContainer = document.createElement('div')
        tempContainer.style.position = 'absolute'
        tempContainer.style.left = '-9999px'
        tempContainer.style.top = '-9999px'
        document.body.appendChild(tempContainer)

        const div = document.createElement('div')
        div.className = 'mermaid'
        div.id = diagramId
        div.textContent = mermaidCode
        tempContainer.appendChild(div)

        // Render mermaid to SVG
        await mermaid.run({
          nodes: [div],
          suppressErrors: false,
        })

        // Get the rendered SVG
        const svgElement = div.querySelector('svg')
        if (!svgElement) {
          throw new Error('No SVG element found after rendering')
        }

        // Get SVG dimensions
        const svgWidth = svgElement.width.baseVal.value || svgElement.viewBox.baseVal.width || 800
        const svgHeight = svgElement.height.baseVal.value || svgElement.viewBox.baseVal.height || 600

        // Ensure SVG has explicit width and height
        if (!svgElement.hasAttribute('width')) {
          svgElement.setAttribute('width', svgWidth.toString())
        }
        if (!svgElement.hasAttribute('height')) {
          svgElement.setAttribute('height', svgHeight.toString())
        }

        // Convert SVG to base64 data URL
        // We'll use SVG directly as it works perfectly for display and zoom/pan
        const svgData = new XMLSerializer().serializeToString(svgElement)
        const svgDataUrl = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)))
        
        // Use SVG directly - it works great as an image and avoids CORS issues
        setImageUrl(svgDataUrl)

        // Cleanup
        setTimeout(() => {
          document.body.removeChild(tempContainer)
        }, 1000)

      } catch (error) {
        console.error('Mermaid rendering error:', error)
        setRenderError('Failed to render diagram. The generated code might be invalid.')
        setImageUrl('')
      }
    }

    renderDiagram()
  }, [mermaidCode, diagramId])

  // Reset zoom/pan tracking flags when diagram changes
  useEffect(() => {
    zoomRecordedRef.current = null
    panRecordedRef.current = null
    // Reset zoom/pan state when diagram changes
    setScale(1)
    setPosition({ x: 0, y: 0 })
  }, [mermaidCode, diagramId])

  // Cleanup zoom tracking timeout on unmount
  useEffect(() => {
    return () => {
      if (zoomTrackTimeoutRef.current) {
        clearTimeout(zoomTrackTimeoutRef.current)
      }
    }
  }, [])

  // Zoom functions
  const handleZoomIn = useCallback(() => {
    if (zoomEnabled) {
      const newScale = Math.min(scale + 0.2, 5)
      setScale(newScale)
      // Track zoom action only once per diagram session
      if (zoomRecordedRef.current !== effectiveDiagramId) {
        trackZoomToggle(true, effectiveDiagramId, mermaidCode)
        zoomRecordedRef.current = effectiveDiagramId
      }
    }
  }, [zoomEnabled, scale, effectiveDiagramId, mermaidCode])

  const handleZoomOut = useCallback(() => {
    if (zoomEnabled) {
      const newScale = Math.max(scale - 0.2, 0.1)
      setScale(newScale)
      // Track zoom action only once per diagram session
      if (zoomRecordedRef.current !== effectiveDiagramId) {
        trackZoomToggle(true, effectiveDiagramId, mermaidCode)
        zoomRecordedRef.current = effectiveDiagramId
      }
    }
  }, [zoomEnabled, scale, effectiveDiagramId, mermaidCode])

  const handleReset = useCallback(() => {
    setScale(1)
    setPosition({ x: 0, y: 0 })
  }, [])

  // Toggle zoom mode (for UI control, but don't track this)
  const handleZoomToggle = useCallback(() => {
    setZoomEnabled(prev => !prev)
  }, [])

  // Toggle pan mode (for UI control, but don't track this)
  const handlePanToggle = useCallback(() => {
    setPanEnabled(prev => {
      const newPanEnabled = !prev
      // Disable dragging when pan is turned off
      if (!newPanEnabled) {
        setIsDragging(false)
      }
      return newPanEnabled
    })
  }, [])

  // Mouse wheel zoom (only when zoom is enabled) - track when user actually zooms
  const handleWheel = useCallback((e: React.WheelEvent) => {
    if (zoomEnabled) {
      e.preventDefault()
      const delta = e.deltaY > 0 ? -0.1 : 0.1
      const newScale = Math.max(0.1, Math.min(5, scale + delta))
      setScale(newScale)
      // Track zoom action only once per diagram session (debounced to avoid too many events)
      if (zoomRecordedRef.current !== effectiveDiagramId) {
        if (zoomTrackTimeoutRef.current) {
          clearTimeout(zoomTrackTimeoutRef.current)
        }
        zoomTrackTimeoutRef.current = setTimeout(() => {
          if (zoomRecordedRef.current !== effectiveDiagramId) {
            trackZoomToggle(true, effectiveDiagramId, mermaidCode)
            zoomRecordedRef.current = effectiveDiagramId
          }
        }, 300) // Track after 300ms of no zoom activity
      }
    }
  }, [zoomEnabled, scale, effectiveDiagramId, mermaidCode])

  // Pan functions (only when pan is enabled) - track when user actually pans
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (panEnabled && e.button === 0) { // Left mouse button
      setIsDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
      // Track pan action only once per diagram session
      if (panRecordedRef.current !== effectiveDiagramId) {
        trackPanToggle(true, effectiveDiagramId, mermaidCode)
        panRecordedRef.current = effectiveDiagramId
      }
    }
  }, [panEnabled, position, effectiveDiagramId, mermaidCode])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (panEnabled && isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }, [panEnabled, isDragging, dragStart])

  const handleMouseUp = useCallback(() => {
    if (panEnabled) {
      setIsDragging(false)
    }
  }, [panEnabled])

  // Touch support for mobile (only when pan is enabled) - track when user actually pans
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (panEnabled && e.touches.length === 1) {
      const touch = e.touches[0]
      setIsDragging(true)
      setDragStart({ x: touch.clientX - position.x, y: touch.clientY - position.y })
      // Track pan action only once per diagram session
      if (panRecordedRef.current !== effectiveDiagramId) {
        trackPanToggle(true, effectiveDiagramId, mermaidCode)
        panRecordedRef.current = effectiveDiagramId
      }
    }
  }, [panEnabled, position, effectiveDiagramId, mermaidCode])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (panEnabled && isDragging && e.touches.length === 1) {
      const touch = e.touches[0]
      setPosition({
        x: touch.clientX - dragStart.x,
        y: touch.clientY - dragStart.y
      })
    }
  }, [panEnabled, isDragging, dragStart])

  const handleTouchEnd = useCallback(() => {
    if (panEnabled) {
      setIsDragging(false)
    }
  }, [panEnabled])

  // Copy mermaid code to clipboard
  const handleCopyCode = useCallback(async () => {
    if (!mermaidCode) return
    
    try {
      await navigator.clipboard.writeText(mermaidCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      // Track the action
      trackMermaidCopy(effectiveDiagramId, mermaidCode)
    } catch (err) {
      console.error('Failed to copy code:', err)
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = mermaidCode
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
        // Track the action
        trackMermaidCopy(effectiveDiagramId, mermaidCode)
      } catch (fallbackErr) {
        console.error('Fallback copy failed:', fallbackErr)
      }
      document.body.removeChild(textArea)
    }
  }, [mermaidCode, diagramId])

  const hasMultipleVariations = variations && variations.length > 1

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col h-full">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            {hasMultipleVariations ? 'Select a Variation' : 'Diagram Preview'}
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            {hasMultipleVariations 
              ? 'Choose one of the generated variations to continue' 
              : 'Zoom and pan to explore the diagram'}
          </p>
        </div>
        <div className="flex gap-2">
          {hasMultipleVariations && onConfirmSelection && selectedVariationIndex !== null && (
            <button
              onClick={() => {
                onConfirmSelection?.()
                // Track the actual selection when "Use This One" is clicked
                if (variations && variations[selectedVariationIndex]) {
                  trackVariationSelection(selectedVariationIndex, effectiveDiagramId, variations[selectedVariationIndex], variations)
                  // Reset zoom/pan tracking when variation is selected
                  zoomRecordedRef.current = null
                  panRecordedRef.current = null
                }
              }}
              className="px-4 py-1.5 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Use This One
            </button>
          )}
          {mermaidCode && !hasMultipleVariations && (
            <button
              onClick={handleCopyCode}
              className="px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors flex items-center gap-1.5"
              title="Copy Mermaid code to clipboard"
            >
              {copied ? (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy Code
                </>
              )}
            </button>
          )}
          {imageUrl && !hasMultipleVariations && (
            <a
              href={imageUrl}
              download="diagram.svg"
              onClick={() => trackImageCopy(effectiveDiagramId, mermaidCode)}
              className="px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
            >
              Download SVG
            </a>
          )}
        </div>
      </div>

      {/* Variations Selector */}
      {hasMultipleVariations && (
        <div className="mb-4">
          <div className="grid grid-cols-3 gap-3">
            {variations.map((variation, index) => (
              <VariationThumbnail
                key={index}
                mermaidCode={variation}
                index={index}
                isSelected={selectedVariationIndex === index}
                onSelect={() => {
                  onSelectVariation?.(index)
                  trackVariationHover(index, effectiveDiagramId, variation, variations)
                  // Reset zoom/pan tracking when variation is hovered
                  zoomRecordedRef.current = null
                  panRecordedRef.current = null
                }}
                diagramId={effectiveDiagramId}
              />
            ))}
          </div>
        </div>
      )}

      <div 
        ref={containerRef}
        className={`flex-1 border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 overflow-hidden relative ${
          panEnabled ? 'cursor-move' : 'cursor-default'
        } ${hasMultipleVariations ? 'min-h-[300px]' : 'min-h-[400px]'}`}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <svg className="animate-spin h-8 w-8 text-primary-600 mx-auto mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-sm text-gray-600">Generating diagram...</p>
            </div>
          </div>
        ) : renderError ? (
          <div className="absolute inset-0 flex items-center justify-center p-6">
            <div className="text-center max-w-md">
              <div className="text-red-600 mb-3">
                <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-red-900 mb-2">{renderError}</p>
              <details className="mt-4 text-left">
                <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-900">Show code</summary>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-xs overflow-auto max-h-48 text-gray-800">
                  {mermaidCode}
                </pre>
              </details>
            </div>
          </div>
        ) : imageUrl ? (
          <>
            <div className="absolute top-2 right-2 z-10 flex flex-col gap-2 bg-white/90 backdrop-blur-sm rounded-lg p-2 shadow-lg border border-gray-200">
              {/* Zoom Toggle Button */}
              <button
                onClick={handleZoomToggle}
                className={`p-2 rounded transition-colors ${
                  zoomEnabled 
                    ? 'bg-primary-100 text-primary-700 hover:bg-primary-200' 
                    : 'hover:bg-gray-100 text-gray-600'
                }`}
                title={zoomEnabled ? "Zoom Enabled - Click to disable" : "Zoom Disabled - Click to enable"}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
                </svg>
              </button>
              {/* Pan Toggle Button */}
              <button
                onClick={handlePanToggle}
                className={`p-2 rounded transition-colors ${
                  panEnabled 
                    ? 'bg-primary-100 text-primary-700 hover:bg-primary-200' 
                    : 'hover:bg-gray-100 text-gray-600'
                }`}
                title={panEnabled ? "Pan Enabled - Click to disable" : "Pan Disabled - Click to enable"}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16l-4-4m0 0l4-4m-4 4h18" />
                </svg>
              </button>
              {/* Zoom In Button (only active when zoom is enabled) */}
              <button
                onClick={handleZoomIn}
                disabled={!zoomEnabled}
                className={`p-2 rounded transition-colors ${
                  zoomEnabled 
                    ? 'hover:bg-gray-100' 
                    : 'opacity-50 cursor-not-allowed'
                }`}
                title={zoomEnabled ? "Zoom In (or scroll up)" : "Enable zoom first"}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
              {/* Zoom Out Button (only active when zoom is enabled) */}
              <button
                onClick={handleZoomOut}
                disabled={!zoomEnabled}
                className={`p-2 rounded transition-colors ${
                  zoomEnabled 
                    ? 'hover:bg-gray-100' 
                    : 'opacity-50 cursor-not-allowed'
                }`}
                title={zoomEnabled ? "Zoom Out (or scroll down)" : "Enable zoom first"}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              {/* Reset Button */}
              <button
                onClick={handleReset}
                className="p-2 hover:bg-gray-100 rounded transition-colors"
                title="Reset View"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
            <div 
              className="absolute inset-0 flex items-center justify-center"
              style={{
                transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
                transformOrigin: 'center center',
                transition: isDragging ? 'none' : 'transform 0.1s ease-out'
              }}
            >
              <img
                ref={imageRef}
                src={imageUrl}
                alt="Generated diagram"
                className="max-w-none select-none"
                style={{ imageRendering: 'crisp-edges' }}
                draggable={false}
                onDoubleClick={handleReset}
              />
            </div>
            <div className="absolute bottom-2 left-2 z-10 bg-white/90 backdrop-blur-sm rounded-lg px-3 py-1.5 text-xs text-gray-600 shadow-sm border border-gray-200">
              Zoom: {Math.round(scale * 100)}% | Drag to pan | Scroll to zoom
            </div>
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <svg className="h-16 w-16 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-sm">Enter a prompt to generate a diagram</p>
            </div>
          </div>
        )}
      </div>
      <div ref={svgRef} className="hidden"></div>
      
      {/* Feedback Panel - Show only when diagram is displayed */}
      {mermaidCode && !hasMultipleVariations && !isLoading && (
        <div className="mt-4">
          <FeedbackPanel diagramId={effectiveDiagramId} mermaidCode={mermaidCode} />
        </div>
      )}
    </div>
  )
}

