import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Diagram AI',
  description: 'Generate UML diagrams from natural language prompts',
  icons: {
    icon: '/favicon.svg',
  },
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

