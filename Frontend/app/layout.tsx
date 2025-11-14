import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Mermaid Diagram Generator',
  description: 'Generate UML diagrams from natural language prompts',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}

