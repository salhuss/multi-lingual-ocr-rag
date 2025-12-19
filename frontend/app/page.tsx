'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'

export default function Home() {
  return (
    <main style={styles.main}>
      <div style={styles.container}>
        <header style={styles.header}>
          <h1 style={styles.title}>Hajj Knowledge Assistant</h1>
          <p style={styles.subtitle}>
            Ask questions about Hajj (Islamic pilgrimage) in English.
            Answers are strictly based on authentic Arabic reference books.
          </p>
        </header>
        <ChatInterface />
      </div>
    </main>
  )
}

const styles = {
  main: {
    minHeight: '100vh',
    padding: '2rem',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  } as React.CSSProperties,
  container: {
    width: '100%',
    maxWidth: '900px',
    backgroundColor: 'white',
    borderRadius: '16px',
    boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
    overflow: 'hidden',
  } as React.CSSProperties,
  header: {
    padding: '2rem',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    textAlign: 'center',
  } as React.CSSProperties,
  title: {
    fontSize: '2rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
  } as React.CSSProperties,
  subtitle: {
    fontSize: '0.95rem',
    opacity: 0.95,
    lineHeight: '1.5',
  } as React.CSSProperties,
}
