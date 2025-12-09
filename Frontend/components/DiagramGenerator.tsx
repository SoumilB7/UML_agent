import { useState, useEffect, useRef } from 'react'
import PromptInput from './PromptInput'
import DiagramDisplay from './DiagramDisplay'
import SettingsModal from './SettingsModal'
import ImportModal from './ImportModal'
import {
  trackNewButton,
  // trackTabAway,
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
  const [isImportOpen, setIsImportOpen] = useState(false)
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

  const handleImport = (code: string) => {
    setMermaidCode(code)
    setIsEditing(true)
    setVariations([])
    setSelectedVariationIndex(null)
    // Generate new ID for imported diagram
    setDiagramId(generateDiagramId())
    // Track as new diagram (conceptually)
    trackNewButton(diagramId, code)
  }

  return (
    <div className="min-h-screen flex flex-col bg-claude-bg text-claude-text-primary font-serif">
      {/* Header */}
      <header className="border-b border-claude-border bg-claude-card sticky top-0 z-50 shadow-sm flex-none">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center shadow-md shrink-0">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold font-serif text-claude-text-primary tracking-tight">
                Diagram AI
              </h1>
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-xs text-gray-500 font-medium hidden sm:block">Intelligent UML Generation</p>
                <span className="text-[10px] px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded-full border border-primary-200 font-medium whitespace-nowrap" title="Your API key is stored locally in your browser">
                  BYOK Secured
                </span>
                <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded-full border border-gray-200 font-medium">
                  v1.0.0
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsImportOpen(true)}
              className="px-3 py-2 sm:px-4 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 transition-all shadow-sm flex items-center gap-2 relative z-10 active:scale-95 duration-100"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              <span className="hidden sm:inline">Import</span>
            </button>
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors relative z-10 active:scale-95 duration-100"
              title="Settings"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content - Flex col on mobile, Side-by-side on LG screens */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8 lg:overflow-hidden lg:h-[calc(100vh-80px)]">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-auto lg:h-full">
          {/* Left Panel - Input (Scrolls on mobile, fixed height on desktop) */}
          <div className="flex flex-col h-auto lg:h-full lg:overflow-hidden order-1 relative z-10">
            <PromptInput
              onGenerate={handleGenerate}
              onNew={handleNew}
              isLoading={isLoading}
              error={error}
              hasExistingDiagram={!!mermaidCode && isEditing}
              diagramId={diagramId}
              currentPrompt={currentPrompt}
            />
          </div>

          {/* Right Panel - Diagram (Scrolls on mobile, fixed height on desktop) */}
          <div className="flex flex-col h-[500px] lg:h-full lg:overflow-hidden order-2 mb-6 lg:mb-0">
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

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-sm border-t border-primary-100 py-4 mt-auto flex-none">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-sm text-gray-500 font-medium flex items-center justify-center gap-1">
            Made with <span className="text-primary-500 animate-pulse">♥️</span> by <span className="font-bold text-gray-700">SoumilB7</span>
            <span className="mx-2 text-gray-300">|</span>
            <a href="/about" className="hover:text-primary-600 transition-colors">About & Benchmarks</a>
          </p>
        </div>
      </footer>

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

      <ImportModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        onImport={handleImport}
      />
    </div>
  )
}

