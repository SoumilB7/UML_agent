'use client'

import { useState } from 'react'
import DiagramGenerator from '@/components/DiagramGenerator'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50">
      <DiagramGenerator />
    </main>
  )
}

