const AUTH_TOKEN_KEY = 'geekz.auth.token'

export function getStoredAuthToken() {
  return window.localStorage.getItem(AUTH_TOKEN_KEY)
}

export function storeAuthToken(token: string) {
  window.localStorage.setItem(
    AUTH_TOKEN_KEY,
    token,
  )
}

export function clearStoredAuthToken() {
  window.localStorage.removeItem(
    AUTH_TOKEN_KEY,
  )
}
