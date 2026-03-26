import type { WsStatus } from '@/types/conversation'
import type { WsServerMessage } from '@/types/api'

type StatusChangeCallback = (status: WsStatus) => void
type MessageCallback = (msg: WsServerMessage) => void

const MAX_RECONNECT_ATTEMPTS = 5

function getWsBaseUrl(): string {
  try {
    const raw = localStorage.getItem('cse-settings')
    if (raw) {
      const parsed = JSON.parse(raw) as { state?: { apiBaseUrl?: string } }
      const url = parsed?.state?.apiBaseUrl
      if (url) return url.replace(/^http/, 'ws').replace(/\/$/, '')
    }
  } catch {
    // ignore
  }
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8003'
  return base.replace(/^http/, 'ws').replace(/\/$/, '')
}

export class SupportWebSocket {
  private ws: WebSocket | null = null
  private conversationId: string
  private onMessage: MessageCallback
  private onStatusChange: StatusChangeCallback
  private reconnectAttempt = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private intentionallyClosed = false

  constructor(
    conversationId: string,
    onMessage: MessageCallback,
    onStatusChange: StatusChangeCallback
  ) {
    this.conversationId = conversationId
    this.onMessage = onMessage
    this.onStatusChange = onStatusChange
    this.connect()
  }

  private connect() {
    const url = `${getWsBaseUrl()}/ws/${this.conversationId}`
    this.onStatusChange(this.reconnectAttempt > 0 ? 'reconnecting' : 'connecting')

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      this.reconnectAttempt = 0
      this.onStatusChange('open')
    }

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as WsServerMessage
        this.onMessage(data)
      } catch {
        // Ignore malformed frames
      }
    }

    this.ws.onerror = () => {
      this.onStatusChange('error')
    }

    this.ws.onclose = () => {
      if (this.intentionallyClosed) {
        this.onStatusChange('closed')
        return
      }
      if (this.reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempt), 30_000)
        this.reconnectAttempt++
        this.onStatusChange('reconnecting')
        this.reconnectTimer = setTimeout(() => this.connect(), delay)
      } else {
        this.onStatusChange('error')
      }
    }
  }

  send(message: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ message }))
    }
  }

  close() {
    this.intentionallyClosed = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
  }

  get status(): WsStatus {
    if (!this.ws) return 'idle'
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting'
      case WebSocket.OPEN: return 'open'
      case WebSocket.CLOSING:
      case WebSocket.CLOSED: return this.intentionallyClosed ? 'closed' : 'reconnecting'
      default: return 'idle'
    }
  }
}
