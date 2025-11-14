'use client'

import { useState, useEffect, useRef } from 'react'
import PromptInput from './PromptInput'
import DiagramDisplay from './DiagramDisplay'
import { 
  trackNewButton, 
  trackTabAway, 
  trackDiagramGenerated, 
  trackDiagramEdited 
} from '@/utils/rlTracking'

const GENERATE_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const EDIT_API_URL = `${GENERATE_API_URL}/diagram/edit`
const GENERATE_URL = `${GENERATE_API_URL}/diagram/generate`

// Generate a unique diagram ID
function generateDiagramId(): string {
  return `diagram-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export default function DiagramGenerator() {
  const [mermaidCode, setMermaidCode] = useState<string>('')
  const [variations, setVariations] = useState<string[]>([])
  const [selectedVariationIndex, setSelectedVariationIndex] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [isEditing, setIsEditing] = useState(false)
  const [diagramId, setDiagramId] = useState<string>(generateDiagramId())
  const [currentPrompt, setCurrentPrompt] = useState<string>('')
  const previousMermaidCodeRef = useRef<string>('')

  const handleGenerate = async (prompt: string, numVariations: number = 1) => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setIsLoading(true)
    setError('')
    setVariations([])
    setSelectedVariationIndex(null)
    
    // Store previous mermaid code for tracking
    previousMermaidCodeRef.current = mermaidCode
    const isEdit = mermaidCode && isEditing
    const previousPrompt = currentPrompt
    setCurrentPrompt(prompt)

    try {
      // If we have existing code, use edit endpoint, otherwise use generate
      const url = isEdit ? EDIT_API_URL : GENERATE_URL
      const body = isEdit
        ? { prompt, existing_mermaid_code: mermaidCode }
        : { prompt, num_variations: numVariations }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to process diagram')
      }

      const data = await response.json()
      
      // Handle multiple variations
      let newMermaidCode: string
      if (data.variations && data.variations.length > 1) {
        setVariations(data.variations)
        newMermaidCode = data.variations[0] // Show first variation by default
        setMermaidCode(newMermaidCode)
        setSelectedVariationIndex(0)
      } else {
        newMermaidCode = data.mermaid_code || ''
        setMermaidCode(newMermaidCode)
        setVariations([])
        setSelectedVariationIndex(null)
      }
      
      // Track the action
      if (isEdit) {
        trackDiagramEdited(prompt, newMermaidCode, diagramId, previousMermaidCodeRef.current)
      } else {
        trackDiagramGenerated(prompt, newMermaidCode, diagramId, numVariations)
      }
      
      setIsEditing(true) // After first generation, subsequent calls will be edits
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectVariation = (index: number) => {
    if (variations[index]) {
      setMermaidCode(variations[index])
      setSelectedVariationIndex(index)
    }
  }

  const handleConfirmSelection = () => {
    // When user confirms selection, clear variations and keep only the selected one
    if (selectedVariationIndex !== null && variations[selectedVariationIndex]) {
      setMermaidCode(variations[selectedVariationIndex])
      setVariations([])
      setSelectedVariationIndex(null)
    }
  }

  const handleNew = () => {
    // Track new button click
    trackNewButton(diagramId, mermaidCode)
    
    // Generate new diagram ID for new session
    setDiagramId(generateDiagramId())
    setMermaidCode('')
    setVariations([])
    setSelectedVariationIndex(null)
    setIsEditing(false)
    setError('')
    setCurrentPrompt('')
    previousMermaidCodeRef.current = ''
  }
  
  // Track tab visibility changes (when user clicks away)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden && mermaidCode) {
        // User clicked away from tab
        trackTabAway(diagramId, mermaidCode)
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [diagramId, mermaidCode])

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Mermaid Diagram Generator</h1>
          <p className="text-sm text-gray-600 mt-1">Transform your ideas into UML diagrams</p>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-180px)]">
          {/* Left Panel - Input */}
          <div className="flex flex-col">
            <PromptInput 
              onGenerate={handleGenerate}
              onNew={handleNew}
              isLoading={isLoading}
              error={error}
              hasExistingDiagram={!!mermaidCode && isEditing}
              diagramId={diagramId}
            />
          </div>

          {/* Right Panel - Diagram */}
          <div className="flex flex-col">
            <DiagramDisplay 
              mermaidCode={mermaidCode} 
              isLoading={isLoading}
              variations={variations}
              selectedVariationIndex={selectedVariationIndex}
              onSelectVariation={handleSelectVariation}
              onConfirmSelection={handleConfirmSelection}
              diagramId={diagramId}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

