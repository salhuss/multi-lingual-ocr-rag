'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'

export default function Home() {
  return (
    <main style={styles.main}>
      {/* Animated background elements */}
      <div style={styles.bgOverlay} />
      <div style={styles.bgPattern} />

      <div style={styles.container}>
        <header style={styles.header}>
          <div style={styles.iconContainer}>
            <svg style={styles.icon} viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 style={styles.title}>Hajj Knowledge Assistant</h1>
          <p style={styles.subtitle}>
            Your trusted companion for authentic Hajj guidance
          </p>
          <div style={styles.badge}>
            <span style={styles.badgeDot}></span>
            <span style={styles.badgeText}>Powered by Arabic Reference Books</span>
          </div>
        </header>

        <ChatInterface />

        <footer style={styles.footer}>
          <p style={styles.footerText}>
            Answers are sourced from authenticated Islamic texts • Always verify with qualified scholars
          </p>
        </footer>
      </div>
    </main>
  )
}

const styles = {
  main: {
    minHeight: '100vh',
    padding: '2rem 1rem',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
    overflow: 'hidden',
  } as React.CSSProperties,
  bgOverlay: {
    position: 'absolute',
    inset: 0,
    background: 'radial-gradient(circle at 20% 50%, rgba(16, 185, 129, 0.15) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(59, 130, 246, 0.15) 0%, transparent 50%)',
    pointerEvents: 'none',
  } as React.CSSProperties,
  bgPattern: {
    position: 'absolute',
    inset: 0,
    backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
    opacity: 0.4,
    pointerEvents: 'none',
  } as React.CSSProperties,
  container: {
    width: '100%',
    maxWidth: '1000px',
    position: 'relative',
    zIndex: 1,
  } as React.CSSProperties,
  header: {
    padding: '3rem 2.5rem',
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(20px)',
    borderRadius: '24px 24px 0 0',
    borderBottom: '1px solid rgba(16, 185, 129, 0.1)',
    textAlign: 'center',
    position: 'relative',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
  } as React.CSSProperties,
  iconContainer: {
    width: '64px',
    height: '64px',
    margin: '0 auto 1.5rem',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    borderRadius: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 10px 30px rgba(16, 185, 129, 0.3)',
    animation: 'float 3s ease-in-out infinite',
  } as React.CSSProperties,
  icon: {
    width: '36px',
    height: '36px',
    color: 'white',
  } as React.CSSProperties,
  title: {
    fontSize: '2.5rem',
    fontWeight: '700',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    marginBottom: '0.75rem',
    letterSpacing: '-0.02em',
  } as React.CSSProperties,
  subtitle: {
    fontSize: '1.1rem',
    color: '#64748b',
    lineHeight: '1.6',
    maxWidth: '600px',
    margin: '0 auto 1.5rem',
  } as React.CSSProperties,
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.5rem 1rem',
    background: 'rgba(16, 185, 129, 0.1)',
    borderRadius: '100px',
    fontSize: '0.875rem',
    color: '#059669',
    fontWeight: '500',
  } as React.CSSProperties,
  badgeDot: {
    width: '6px',
    height: '6px',
    background: '#10b981',
    borderRadius: '50%',
    animation: 'pulse 2s ease-in-out infinite',
  } as React.CSSProperties,
  badgeText: {
    letterSpacing: '0.02em',
  } as React.CSSProperties,
  footer: {
    padding: '1.5rem 2.5rem',
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(20px)',
    borderRadius: '0 0 24px 24px',
    borderTop: '1px solid rgba(16, 185, 129, 0.1)',
    textAlign: 'center',
    boxShadow: '0 -4px 6px -1px rgba(0, 0, 0, 0.05)',
  } as React.CSSProperties,
  footerText: {
    fontSize: '0.875rem',
    color: '#94a3b8',
    lineHeight: '1.5',
  } as React.CSSProperties,
}
