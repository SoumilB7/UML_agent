'use client'

import { useState, FormEvent, useEffect, useRef } from 'react'
import { trackPromptUpdate } from '@/utils/rlTracking'

interface PromptInputProps {
  onGenerate: (prompt: string, numVariations: number) => void
  onNew: () => void
  isLoading: boolean
  error: string
  hasExistingDiagram: boolean
  diagramId?: string
}

const EXAMPLE_PROMPTS = [
  'Create a class diagram for an e-commerce system with User, Product, Order, and Payment classes',
  'Create a sequence diagram for user login process',
  'Create a class diagram for a library management system',
  'Create a class diagram for a banking system with Account, Transaction, and Customer classes',
]

export default function PromptInput({ onGenerate, onNew, isLoading, error, hasExistingDiagram, diagramId, currentPrompt }: PromptInputProps & { currentPrompt?: string }) {
  const [prompt, setPrompt] = useState('')
  const [generateMany, setGenerateMany] = useState(false)
  const previousPromptRef = useRef<string>('')

  // Update local prompt state when currentPrompt prop changes (e.g. from parent state update)
  useEffect(() => {
    if (currentPrompt !== undefined && currentPrompt !== prompt) {
      setPrompt(currentPrompt)
    }
  }, [currentPrompt])

  // Track prompt changes when user types
  useEffect(() => {
    if (prompt && prompt !== previousPromptRef.current && previousPromptRef.current) {
      // Only track if there's a previous prompt (user is editing)
      // We'll track significant changes (more than just a few characters)
      if (prompt.length > 10 && Math.abs(prompt.length - previousPromptRef.current.length) > 5) {
        trackPromptUpdate(prompt, previousPromptRef.current, diagramId)
      }
    }
    previousPromptRef.current = prompt
  }, [prompt, diagramId])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const numVariations = generateMany ? 3 : 1
    onGenerate(prompt, numVariations)
  }

  const handleExampleClick = (example: string) => {
    setPrompt(example)
  }

  const handleNewClick = () => {
    setPrompt('')
    onNew()
  }

  return (
    <div className="bg-claude-card rounded-xl shadow-sm border border-claude-border p-4 sm:p-6 flex flex-col h-auto lg:h-full font-serif text-claude-text-primary">
      <div className="mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
          <label htmlFor="prompt" className="block text-sm font-semibold text-claude-text-primary">
            {hasExistingDiagram ? 'Edit your diagram' : 'Enter your prompt'}
          </label>
          <div className="flex items-center gap-3 self-end sm:self-auto">
            {!hasExistingDiagram && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-claude-text-secondary">One</span>
                <button
                  type="button"
                  onClick={() => setGenerateMany(!generateMany)}
                  disabled={isLoading}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${generateMany ? 'bg-primary-600' : 'bg-gray-300'
                    }`}
                  role="switch"
                  aria-checked={generateMany}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${generateMany ? 'translate-x-6' : 'translate-x-1'
                      }`}
                  />
                </button>
                <span className="text-xs text-claude-text-secondary">Many (3)</span>
              </div>
            )}
            {hasExistingDiagram && (
              <button
                onClick={handleNewClick}
                disabled={isLoading}
                className="text-xs font-medium text-primary-600 hover:text-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
              >
                New Diagram
              </button>
            )}
          </div>
        </div>
        {hasExistingDiagram && (
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800">
              💡 You're editing. Describe changes below.
            </p>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={hasExistingDiagram
              ? "Describe the changes you want to make..."
              : "Describe the diagram you want to generate..."}
            className="w-full h-24 sm:h-32 px-4 py-3 bg-white border border-claude-border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm text-claude-text-primary placeholder-gray-400 transition-all font-sans"
            disabled={isLoading}
          />

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm font-sans">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            {hasExistingDiagram && (
              <button
                type="button"
                onClick={handleNewClick}
                disabled={isLoading}
                className="px-4 py-3 border border-claude-border text-claude-text-secondary font-medium rounded-lg hover:bg-claude-bg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-sans"
              >
                New
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="flex-1 bg-gradient-to-r from-primary-600 to-primary-700 text-white font-medium py-3 px-4 rounded-lg hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md font-sans"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {hasExistingDiagram ? 'Update' : 'Generate'}
                </span>
              ) : (
                hasExistingDiagram ? 'Update Diagram' : 'Generate Diagram'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Example Prompts */}
      <div className="mt-2 sm:mt-4 pt-4 border-t border-claude-border flex-1 overflow-y-auto min-h-0 hidden sm:block">
        <p className="text-xs font-medium text-claude-text-secondary uppercase tracking-wide mb-3 sticky top-0 bg-claude-card pb-2">
          Example Prompts
        </p>
        <div className="space-y-2">
          {EXAMPLE_PROMPTS.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="w-full text-left px-3 py-2 text-sm text-claude-text-primary bg-claude-bg hover:bg-[#e8e2dc] rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-transparent font-sans"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

