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

  return (
    <div style={styles.chatContainer}>
      <div style={styles.messagesContainer}>
        {messages.length === 0 && (
          <div style={styles.emptyState}>
            <p style={styles.emptyTitle}>Welcome! Ask me about Hajj.</p>
            <div style={styles.exampleQuestions}>
              <p style={styles.exampleLabel}>Example questions:</p>
              <button
                style={styles.exampleButton}
                onClick={() => setInput('How do I perform tawaf?')}
              >
                How do I perform tawaf?
              </button>
              <button
                style={styles.exampleButton}
                onClick={() => setInput('What are the types of Hajj?')}
              >
                What are the types of Hajj?
              </button>
              <button
                style={styles.exampleButton}
                onClick={() => setInput('What is the significance of Arafat?')}
              >
                What is the significance of Arafat?
              </button>
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
            <div
              style={{
                ...styles.message,
                ...(message.role === 'user' ? styles.userMessage : styles.assistantMessage),
              }}
            >
              <p style={styles.messageContent}>{message.content}</p>

              {message.citations && message.citations.length > 0 && (
                <div style={styles.citationsContainer}>
                  <p style={styles.citationsTitle}>Sources:</p>
                  {message.citations.map((citation, citIndex) => (
                    <div key={citIndex} style={styles.citation}>
                      <p style={styles.citationMeta}>
                        <strong>{citation.book}</strong> - Page {citation.page}
                      </p>
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
            <div style={{ ...styles.message, ...styles.assistantMessage }}>
              <div style={styles.loadingDots}>
                <span>.</span>
                <span>.</span>
                <span>.</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} style={styles.inputForm}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about Hajj..."
          style={styles.input}
          disabled={isLoading}
        />
        <button
          type="submit"
          style={{
            ...styles.sendButton,
            ...(isLoading || !input.trim() ? styles.sendButtonDisabled : {}),
          }}
          disabled={isLoading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  )
}

const styles = {
  chatContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '600px',
  } as React.CSSProperties,
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  } as React.CSSProperties,
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#666',
  } as React.CSSProperties,
  emptyTitle: {
    fontSize: '1.2rem',
    marginBottom: '2rem',
    color: '#333',
  } as React.CSSProperties,
  exampleQuestions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    alignItems: 'center',
  } as React.CSSProperties,
  exampleLabel: {
    fontSize: '0.9rem',
    color: '#666',
    marginBottom: '0.5rem',
  } as React.CSSProperties,
  exampleButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#f0f0f0',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '0.9rem',
    transition: 'background-color 0.2s',
  } as React.CSSProperties,
  messageWrapper: {
    display: 'flex',
    width: '100%',
  } as React.CSSProperties,
  message: {
    maxWidth: '80%',
    padding: '1rem',
    borderRadius: '12px',
    wordWrap: 'break-word',
  } as React.CSSProperties,
  userMessage: {
    backgroundColor: '#667eea',
    color: 'white',
    marginLeft: 'auto',
  } as React.CSSProperties,
  assistantMessage: {
    backgroundColor: '#f5f5f5',
    color: '#333',
  } as React.CSSProperties,
  messageContent: {
    lineHeight: '1.5',
    marginBottom: '0.5rem',
  } as React.CSSProperties,
  citationsContainer: {
    marginTop: '1rem',
    paddingTop: '1rem',
    borderTop: '1px solid #ddd',
  } as React.CSSProperties,
  citationsTitle: {
    fontSize: '0.85rem',
    fontWeight: 'bold',
    marginBottom: '0.5rem',
    color: '#555',
  } as React.CSSProperties,
  citation: {
    marginTop: '0.75rem',
    padding: '0.75rem',
    backgroundColor: 'white',
    borderRadius: '6px',
    border: '1px solid #e0e0e0',
  } as React.CSSProperties,
  citationMeta: {
    fontSize: '0.85rem',
    color: '#667eea',
    marginBottom: '0.5rem',
  } as React.CSSProperties,
  citationExcerpt: {
    fontSize: '0.9rem',
    color: '#555',
    fontStyle: 'italic',
    lineHeight: '1.8',
  } as React.CSSProperties,
  loadingDots: {
    display: 'flex',
    gap: '0.25rem',
  } as React.CSSProperties,
  inputForm: {
    display: 'flex',
    gap: '0.5rem',
    padding: '1.5rem',
    borderTop: '1px solid #e0e0e0',
    backgroundColor: '#fafafa',
  } as React.CSSProperties,
  input: {
    flex: 1,
    padding: '0.75rem 1rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '1rem',
    outline: 'none',
  } as React.CSSProperties,
  sendButton: {
    padding: '0.75rem 2rem',
    backgroundColor: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  } as React.CSSProperties,
  sendButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  } as React.CSSProperties,
}
