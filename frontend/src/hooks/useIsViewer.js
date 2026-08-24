import useAuthStore from '@/store/authStore'

function getRoleFromToken() {
  try {
    const token = localStorage.getItem('access_token')
    if (!token) return null
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role?.toLowerCase()
  } catch {
    return null
  }
}

export default function useIsViewer() {
  const user = useAuthStore(s => s.user)
  const roleFromStore = user?.role?.toLowerCase()
  const roleFromToken = getRoleFromToken()
  return (roleFromStore || roleFromToken) === 'viewer'
}