'use client'

import { useState, FormEvent } from 'react'

interface PromptInputProps {
  onGenerate: (prompt: string, numVariations: number) => void
  onNew: () => void
  isLoading: boolean
  error: string
  hasExistingDiagram: boolean
}

const EXAMPLE_PROMPTS = [
  'Create a class diagram for an e-commerce system with User, Product, Order, and Payment classes',
  'Create a sequence diagram for user login process',
  'Create a class diagram for a library management system',
  'Create a class diagram for a banking system with Account, Transaction, and Customer classes',
]

export default function PromptInput({ onGenerate, onNew, isLoading, error, hasExistingDiagram }: PromptInputProps) {
  const [prompt, setPrompt] = useState('')
  const [generateMany, setGenerateMany] = useState(false)

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
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col h-full">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label htmlFor="prompt" className="block text-sm font-semibold text-gray-900">
            {hasExistingDiagram ? 'Edit your diagram' : 'Enter your prompt'}
          </label>
          <div className="flex items-center gap-3">
            {!hasExistingDiagram && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-600">One</span>
                <button
                  type="button"
                  onClick={() => setGenerateMany(!generateMany)}
                  disabled={isLoading}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
                    generateMany ? 'bg-primary-600' : 'bg-gray-300'
                  }`}
                  role="switch"
                  aria-checked={generateMany}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      generateMany ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className="text-xs text-gray-600">Many (3)</span>
              </div>
            )}
            {hasExistingDiagram && (
              <button
                onClick={handleNewClick}
                disabled={isLoading}
                className="text-xs font-medium text-primary-600 hover:text-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                New Diagram
              </button>
            )}
          </div>
        </div>
        {hasExistingDiagram && (
          <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-800">
              💡 You're editing an existing diagram. Describe the changes you want to make.
            </p>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder={hasExistingDiagram 
              ? "Describe the changes you want to make to the diagram..." 
              : "Describe the diagram you want to generate..."}
            className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm text-gray-900 placeholder-gray-400 transition-all"
            disabled={isLoading}
          />
          
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            {hasExistingDiagram && (
              <button
                type="button"
                onClick={handleNewClick}
                disabled={isLoading}
                className="px-4 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                New
              </button>
            )}
            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="flex-1 bg-gradient-to-r from-primary-600 to-primary-700 text-white font-medium py-3 px-4 rounded-lg hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {hasExistingDiagram ? 'Updating...' : 'Generating...'}
                </span>
              ) : (
                hasExistingDiagram ? 'Update Diagram' : 'Generate Diagram'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Example Prompts */}
      <div className="mt-auto pt-6 border-t border-gray-200">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
          Example Prompts
        </p>
        <div className="space-y-2">
          {EXAMPLE_PROMPTS.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={isLoading}
              className="w-full text-left px-3 py-2 text-sm text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-transparent hover:border-gray-200"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

