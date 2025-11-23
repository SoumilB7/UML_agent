'use client'

import { useState, useEffect, useRef } from 'react'
import PromptInput from './PromptInput'
import DiagramDisplay from './DiagramDisplay'
import SettingsModal from './SettingsModal'
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
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const previousMermaidCodeRef = useRef<string>('')

  const handleGenerate = async (prompt: string, numVariations: number = 1) => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    // Check for API key
    const apiKey = localStorage.getItem('openai_api_key')
    if (!apiKey) {
      setIsSettingsOpen(true)
      setError('Please enter your OpenAI API key in settings to continue')
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
          'X-OpenAI-Key': apiKey
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Mermaid Diagram Generator</h1>
            <p className="text-sm text-gray-600 mt-1">Transform your ideas into UML diagrams</p>
          </div>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Settings"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
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

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSave={(key) => {
          // Clear error if key is provided
          if (key && error.includes('API key')) {
            setError('')
          }
        }}
      />
    </div>
  )
}

