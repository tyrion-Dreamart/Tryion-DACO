import { create } from 'zustand'
import api from '@/services/api'

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.post('/api/v1/auth/login', { email, password })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      const { data: user } = await api.get('/api/v1/auth/me')
      set({ user, isAuthenticated: true, isLoading: false })
      return true
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : 'Credenciales incorrectas'
      set({ error: msg, isLoading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
    window.location.href = '/login'
  },

  fetchMe: async () => {
    try {
      const { data } = await api.get('/api/v1/auth/me')
      set({ user: data, isAuthenticated: true })
    } catch {
      set({ isAuthenticated: false })
    }
  },
}))

export default useAuthStore