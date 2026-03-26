import axios from 'axios'
import type { StartRequest, StartResponse, HealthResponse } from '@/types/api'

// Read baseURL lazily so Settings changes take effect without a page reload
function getBaseUrl(): string {
  try {
    const raw = localStorage.getItem('cse-settings')
    if (raw) {
      const parsed = JSON.parse(raw) as { state?: { apiBaseUrl?: string } }
      const url = parsed?.state?.apiBaseUrl
      if (url) return url.replace(/\/$/, '')
    }
  } catch {
    // ignore
  }
  return import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8003'
}

const client = axios.create({ timeout: 30_000 })

client.interceptors.request.use((config) => {
  config.baseURL = getBaseUrl()
  return config
})

export interface ApiError {
  message: string
  status?: number
}

client.interceptors.response.use(
  (res) => res,
  (err: unknown) => {
    if (axios.isAxiosError(err)) {
      const message = (err.response?.data as { detail?: string })?.detail ?? err.message
      const error: ApiError = { message, status: err.response?.status }
      return Promise.reject(error)
    }
    return Promise.reject({ message: 'Unknown error' } as ApiError)
  }
)

export const supportApi = {
  start: async (data: StartRequest): Promise<StartResponse> => {
    const res = await client.post<StartResponse>('/support/start', data)
    return res.data
  },

  health: async (): Promise<HealthResponse> => {
    const res = await client.get<HealthResponse>('/health')
    return res.data
  },
}
