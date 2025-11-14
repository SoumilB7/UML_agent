'use client'

import { useState } from 'react'
import PromptInput from './PromptInput'
import DiagramDisplay from './DiagramDisplay'

const GENERATE_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const EDIT_API_URL = `${GENERATE_API_URL}/diagram/edit`
const GENERATE_URL = `${GENERATE_API_URL}/diagram/generate`

export default function DiagramGenerator() {
  const [mermaidCode, setMermaidCode] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [isEditing, setIsEditing] = useState(false)

  const handleGenerate = async (prompt: string) => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      // If we have existing code, use edit endpoint, otherwise use generate
      const url = mermaidCode && isEditing ? EDIT_API_URL : GENERATE_URL
      const body = mermaidCode && isEditing
        ? { prompt, existing_mermaid_code: mermaidCode }
        : { prompt }

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
      setMermaidCode(data.mermaid_code || '')
      setIsEditing(true) // After first generation, subsequent calls will be edits
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNew = () => {
    setMermaidCode('')
    setIsEditing(false)
    setError('')
  }

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
            />
          </div>

          {/* Right Panel - Diagram */}
          <div className="flex flex-col">
            <DiagramDisplay 
              mermaidCode={mermaidCode} 
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

