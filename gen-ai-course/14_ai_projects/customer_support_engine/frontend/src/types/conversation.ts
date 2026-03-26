import type { IssueType, Severity, SupportStatus } from './api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string // ISO
  issueType?: IssueType | null
  severity?: Severity | null
  status?: SupportStatus | null
  isError?: boolean
}

export interface Conversation {
  id: string
  messages: Message[]
  issueType: IssueType | null
  severity: Severity | null
  status: SupportStatus | null
  createdAt: string
  updatedAt: string
}

export interface StoredConversation {
  id: string
  firstMessage: string
  issueType: IssueType | null
  severity: Severity | null
  status: SupportStatus | null
  messageCount: number
  createdAt: string
  updatedAt: string
  messages: Message[]
}

export type WsStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed' | 'error'
