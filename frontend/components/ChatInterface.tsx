'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Citation {
  book: string
  page: number
  excerpt: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  status?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        query: input,
        use_arabic_translation: true,
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        citations: response.data.citations || [],
        status: response.data.status,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error: any) {
      const errorMessage: Message = {
        role: 'assistant',
        content: error.response?.data?.detail || 'Error: Could not connect to the server. Please try again.',
        status: 'error',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const exampleQuestions = [
    { text: 'How do I perform tawaf?', icon: '🕋' },
    { text: 'What are the types of Hajj?', icon: '📖' },
    { text: 'What is the significance of Arafat?', icon: '⛰️' },
  ]

  return (
    <div style={styles.chatContainer}>
      <div style={styles.messagesContainer}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>
              <svg style={styles.emptyIconSvg} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 style={styles.emptyTitle}>Start Your Journey</h3>
            <p style={styles.emptyDesc}>Ask any question about Hajj rituals, rules, and guidance</p>

            <div style={styles.exampleQuestions}>
              {exampleQuestions.map((q, i) => (
                <button
                  key={i}
                  style={styles.exampleButton}
                  onClick={() => setInput(q.text)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 20px rgba(16, 185, 129, 0.15)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.05)'
                  }}
                >
                  <span style={styles.exampleIcon}>{q.icon}</span>
                  <span style={styles.exampleText}>{q.text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              ...styles.messageWrapper,
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            {message.role === 'assistant' && (
              <div style={styles.avatar}>
                <svg style={styles.avatarIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
            )}

            <div
              style={{
                ...styles.message,
                ...(message.role === 'user' ? styles.userMessage : styles.assistantMessage),
              }}
            >
              <p style={styles.messageContent}>{message.content}</p>

              {message.citations && message.citations.length > 0 && (
                <div style={styles.citationsContainer}>
                  <div style={styles.citationsHeader}>
                    <svg style={styles.citationIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span style={styles.citationsTitle}>Source References</span>
                  </div>
                  {message.citations.map((citation, citIndex) => (
                    <div key={citIndex} style={styles.citation}>
                      <div style={styles.citationHeader}>
                        <span style={styles.citationBook}>{citation.book}</span>
                        <span style={styles.citationPage}>Page {citation.page}</span>
                      </div>
                      {citation.excerpt && (
                        <p style={styles.citationExcerpt} className="arabic">
                          {citation.excerpt}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div style={{ ...styles.messageWrapper, justifyContent: 'flex-start' }}>
            <div style={styles.avatar}>
              <svg style={styles.avatarIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <div style={{ ...styles.message, ...styles.assistantMessage }}>
              <div style={styles.loadingDots}>
                <span style={{...styles.dot, animationDelay: '0s'}}></span>
                <span style={{...styles.dot, animationDelay: '0.2s'}}></span>
                <span style={{...styles.dot, animationDelay: '0.4s'}}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} style={styles.inputForm}>
        <div style={styles.inputWrapper}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about Hajj..."
            style={styles.input}
            disabled={isLoading}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = '#10b981'
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = '#e5e7eb'
              e.currentTarget.style.boxShadow = 'none'
            }}
          />
          <button
            type="submit"
            style={{
              ...styles.sendButton,
              ...(isLoading || !input.trim() ? styles.sendButtonDisabled : {}),
            }}
            disabled={isLoading || !input.trim()}
            onMouseEnter={(e) => {
              if (!isLoading && input.trim()) {
                e.currentTarget.style.transform = 'scale(1.05)'
                e.currentTarget.style.boxShadow = '0 8px 20px rgba(16, 185, 129, 0.4)'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'scale(1)'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.3)'
            }}
          >
            <svg style={styles.sendIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  )
}

const styles = {
  chatContainer: {
    display: 'flex',
    flexDirection: 'column',
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(20px)',
  } as React.CSSProperties,
  messagesContainer: {
    height: '600px',
    overflowY: 'auto',
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  } as React.CSSProperties,
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    textAlign: 'center',
    padding: '2rem',
  } as React.CSSProperties,
  emptyIcon: {
    width: '80px',
    height: '80px',
    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
    borderRadius: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: '1.5rem',
  } as React.CSSProperties,
  emptyIconSvg: {
    width: '40px',
    height: '40px',
    color: '#10b981',
  } as React.CSSProperties,
  emptyTitle: {
    fontSize: '1.5rem',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '0.5rem',
  } as React.CSSProperties,
  emptyDesc: {
    fontSize: '1rem',
    color: '#64748b',
    marginBottom: '2rem',
    maxWidth: '400px',
  } as React.CSSProperties,
  exampleQuestions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
    width: '100%',
    maxWidth: '500px',
  } as React.CSSProperties,
  exampleButton: {
    padding: '1rem 1.5rem',
    background: 'white',
    border: '2px solid #e5e7eb',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '0.95rem',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    textAlign: 'left',
    color: '#334155',
    fontWeight: '500',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  } as React.CSSProperties,
  exampleIcon: {
    fontSize: '1.5rem',
  } as React.CSSProperties,
  exampleText: {
    flex: 1,
  } as React.CSSProperties,
  messageWrapper: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'flex-start',
  } as React.CSSProperties,
  avatar: {
    width: '36px',
    height: '36px',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
  } as React.CSSProperties,
  avatarIcon: {
    width: '20px',
    height: '20px',
    color: 'white',
  } as React.CSSProperties,
  message: {
    maxWidth: '75%',
    padding: '1.25rem',
    borderRadius: '16px',
    wordWrap: 'break-word',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
    animation: 'slideIn 0.3s ease',
  } as React.CSSProperties,
  userMessage: {
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    color: 'white',
    marginLeft: 'auto',
  } as React.CSSProperties,
  assistantMessage: {
    background: 'white',
    color: '#1e293b',
    border: '1px solid #f1f5f9',
  } as React.CSSProperties,
  messageContent: {
    lineHeight: '1.6',
    fontSize: '0.95rem',
  } as React.CSSProperties,
  citationsContainer: {
    marginTop: '1.25rem',
    paddingTop: '1.25rem',
    borderTop: '1px solid #e5e7eb',
  } as React.CSSProperties,
  citationsHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '1rem',
  } as React.CSSProperties,
  citationIcon: {
    width: '18px',
    height: '18px',
    color: '#10b981',
  } as React.CSSProperties,
  citationsTitle: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#059669',
  } as React.CSSProperties,
  citation: {
    marginTop: '0.75rem',
    padding: '1rem',
    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%)',
    borderRadius: '12px',
    border: '1px solid rgba(16, 185, 129, 0.1)',
  } as React.CSSProperties,
  citationHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  } as React.CSSProperties,
  citationBook: {
    fontSize: '0.875rem',
    fontWeight: '600',
    color: '#059669',
  } as React.CSSProperties,
  citationPage: {
    fontSize: '0.75rem',
    color: '#64748b',
    background: 'white',
    padding: '0.25rem 0.75rem',
    borderRadius: '100px',
  } as React.CSSProperties,
  citationExcerpt: {
    fontSize: '0.9rem',
    color: '#475569',
    lineHeight: '1.8',
    fontStyle: 'italic',
  } as React.CSSProperties,
  loadingDots: {
    display: 'flex',
    gap: '0.5rem',
    padding: '0.5rem',
  } as React.CSSProperties,
  dot: {
    width: '8px',
    height: '8px',
    background: '#10b981',
    borderRadius: '50%',
    animation: 'bounce 1.4s infinite ease-in-out',
  } as React.CSSProperties,
  inputForm: {
    padding: '1.5rem 2rem',
    borderTop: '1px solid #e5e7eb',
    background: 'rgba(249, 250, 251, 0.5)',
  } as React.CSSProperties,
  inputWrapper: {
    display: 'flex',
    gap: '0.75rem',
    alignItems: 'center',
  } as React.CSSProperties,
  input: {
    flex: 1,
    padding: '1rem 1.25rem',
    border: '2px solid #e5e7eb',
    borderRadius: '12px',
    fontSize: '0.95rem',
    outline: 'none',
    transition: 'all 0.2s ease',
    background: 'white',
    color: '#1e293b',
  } as React.CSSProperties,
  sendButton: {
    width: '48px',
    height: '48px',
    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    flexShrink: 0,
    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
  } as React.CSSProperties,
  sendIcon: {
    width: '20px',
    height: '20px',
  } as React.CSSProperties,
  sendButtonDisabled: {
    background: '#e5e7eb',
    cursor: 'not-allowed',
    boxShadow: 'none',
  } as React.CSSProperties,
}
