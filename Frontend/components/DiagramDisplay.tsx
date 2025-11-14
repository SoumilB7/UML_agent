'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import mermaid from 'mermaid'

interface DiagramDisplayProps {
  mermaidCode: string
  isLoading: boolean
}

export default function DiagramDisplay({ mermaidCode, isLoading }: DiagramDisplayProps) {
  const svgRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  const [imageUrl, setImageUrl] = useState<string>('')
  const [renderError, setRenderError] = useState<string>('')
  const [diagramId] = useState(() => `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`)
  
  // Zoom and pan state
  const [scale, setScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [copied, setCopied] = useState(false)

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

  // Zoom functions
  const handleZoomIn = useCallback(() => {
    setScale(prev => Math.min(prev + 0.2, 5))
  }, [])

  const handleZoomOut = useCallback(() => {
    setScale(prev => Math.max(prev - 0.2, 0.1))
  }, [])

  const handleReset = useCallback(() => {
    setScale(1)
    setPosition({ x: 0, y: 0 })
  }, [])

  // Mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.1 : 0.1
    setScale(prev => Math.max(0.1, Math.min(5, prev + delta)))
  }, [])

  // Pan functions
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) { // Left mouse button
      setIsDragging(true)
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
    }
  }, [position])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    }
  }, [isDragging, dragStart])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Touch support for mobile
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      const touch = e.touches[0]
      setIsDragging(true)
      setDragStart({ x: touch.clientX - position.x, y: touch.clientY - position.y })
    }
  }, [position])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (isDragging && e.touches.length === 1) {
      const touch = e.touches[0]
      setPosition({
        x: touch.clientX - dragStart.x,
        y: touch.clientY - dragStart.y
      })
    }
  }, [isDragging, dragStart])

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false)
  }, [])

  // Copy mermaid code to clipboard
  const handleCopyCode = useCallback(async () => {
    if (!mermaidCode) return
    
    try {
      await navigator.clipboard.writeText(mermaidCode)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
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
      } catch (fallbackErr) {
        console.error('Fallback copy failed:', fallbackErr)
      }
      document.body.removeChild(textArea)
    }
  }, [mermaidCode])

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col h-full">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">Diagram Preview</h2>
          <p className="text-xs text-gray-500 mt-1">Zoom and pan to explore the diagram</p>
        </div>
        <div className="flex gap-2">
          {mermaidCode && (
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
          {imageUrl && (
            <a
              href={imageUrl}
              download="diagram.svg"
              className="px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors"
            >
              Download SVG
            </a>
          )}
        </div>
      </div>

      <div 
        ref={containerRef}
        className="flex-1 border-2 border-dashed border-gray-200 rounded-lg bg-gray-50 overflow-hidden min-h-[400px] relative cursor-move"
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
              <button
                onClick={handleZoomIn}
                className="p-2 hover:bg-gray-100 rounded transition-colors"
                title="Zoom In (or scroll up)"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
                </svg>
              </button>
              <button
                onClick={handleZoomOut}
                className="p-2 hover:bg-gray-100 rounded transition-colors"
                title="Zoom Out (or scroll down)"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
                </svg>
              </button>
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
              Zoom: {Math.round(scale * 100)}% | Drag to pan
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
    </div>
  )
}

