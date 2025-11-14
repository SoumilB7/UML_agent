'use client'

import { useState } from 'react'
import { trackFeedback } from '@/utils/rlTracking'

interface FeedbackPanelProps {
  diagramId?: string
  mermaidCode?: string
  onFeedbackSubmitted?: () => void
}

export default function FeedbackPanel({ 
  diagramId, 
  mermaidCode,
  onFeedbackSubmitted 
}: FeedbackPanelProps) {
  const [rating, setRating] = useState<number>(0)
  const [hoveredRating, setHoveredRating] = useState<number>(0)
  const [feedbackText, setFeedbackText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleStarClick = (value: number) => {
    setRating(value)
  }

  const handleStarHover = (value: number) => {
    setHoveredRating(value)
  }

  const handleStarLeave = () => {
    setHoveredRating(0)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (rating === 0) {
      return // Require at least 1 star
    }

    setIsSubmitting(true)

    try {
      await trackFeedback(rating, feedbackText, diagramId, mermaidCode)
      setIsSubmitted(true)
      onFeedbackSubmitted?.()
      
      // Reset after a delay
      setTimeout(() => {
        setRating(0)
        setFeedbackText('')
        setIsSubmitted(false)
      }, 3000)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isSubmitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
        <svg className="w-8 h-8 text-green-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <p className="text-sm font-medium text-green-800">Thank you for your feedback!</p>
      </div>
    )
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Rate this diagram</h3>
      
      {/* Star Rating */}
      <div className="flex items-center gap-1 mb-4">
        {[1, 2, 3, 4, 5].map((value) => {
          const isActive = hoveredRating >= value || (!hoveredRating && rating >= value)
          return (
            <button
              key={value}
              type="button"
              onClick={() => handleStarClick(value)}
              onMouseEnter={() => handleStarHover(value)}
              onMouseLeave={handleStarLeave}
              className="focus:outline-none transition-transform hover:scale-110"
              aria-label={`Rate ${value} out of 5`}
            >
              <svg
                className={`w-6 h-6 ${
                  isActive ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'
                } transition-colors`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
          )
        })}
        {rating > 0 && (
          <span className="ml-2 text-xs text-gray-600">
            {rating} {rating === 1 ? 'star' : 'stars'}
          </span>
        )}
      </div>

      {/* Feedback Text Box */}
      <form onSubmit={handleSubmit}>
        <textarea
          value={feedbackText}
          onChange={(e) => setFeedbackText(e.target.value)}
          placeholder="Share your thoughts about this diagram (optional)..."
          className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm text-gray-900 placeholder-gray-400 transition-all mb-3"
          disabled={isSubmitting}
        />
        
        <button
          type="submit"
          disabled={isSubmitting || rating === 0}
          className="w-full px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    </div>
  )
}

