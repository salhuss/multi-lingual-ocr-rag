import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Hajj Knowledge Assistant',
  description: 'Ask questions about Hajj based on authentic Arabic sources',
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
