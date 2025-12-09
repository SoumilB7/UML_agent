import type { Metadata } from 'next'
import { Saira } from 'next/font/google'
import './globals.css'

const saira = Saira({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-saira',
})

export const metadata: Metadata = {
  metadataBase: new URL('https://uml-agent.vercel.app'),
  title: 'Diagram AI - Intelligent UML Diagram Generator',
  description: 'Generate complex UML diagrams, flowcharts, and sequence diagrams instantly using AI. Transform text into professional diagrams with Mermaid.js. Free, secure, and open-source.',
  keywords: 'UML generator, AI diagram, Mermaid.js, flowchart maker, sequence diagram, class diagram, text to diagram, developer tools, documentation',
  authors: [{ name: 'SoumilB7' }],
  creator: 'SoumilB7',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://uml-agent.vercel.app',
    title: 'Diagram AI - Intelligent UML Diagram Generator',
    description: 'Generate complex UML diagrams instantly using AI. Transform text into professional diagrams.',
    siteName: 'Diagram AI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Diagram AI - Intelligent UML Diagram Generator',
    description: 'Generate complex UML diagrams instantly using AI.',
    creator: '@soumilb7',
  },
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
      <body className={`${saira.variable} font-sans antialiased`}>{children}</body>
    </html>
  )
}

