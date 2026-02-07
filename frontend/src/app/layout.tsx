import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Research Agent',
  description: 'AI-powered research agent for tech and investing intelligence',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
