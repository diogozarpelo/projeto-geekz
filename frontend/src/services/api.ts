const API_PREFIX = '/api'

export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(
    message: string,
    status: number,
    payload: unknown = null,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

type ApiMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE'

type ApiRequestOptions = {
  method?: ApiMethod
  signal?: AbortSignal
  token?: string | null
  body?: unknown
}

function getApiErrorMessage(
  payload: unknown,
  status: number,
) {
  if (
    typeof payload === 'object'
    && payload !== null
    && 'detail' in payload
    && typeof payload.detail === 'string'
  ) {
    return payload.detail
  }

  return `API request failed with status ${status}.`
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const headers = new Headers({
    Accept: 'application/json',
  })

  if (options.token) {
    headers.set(
      'Authorization',
      `Token ${options.token}`,
    )
  }

  if (options.body !== undefined) {
    headers.set(
      'Content-Type',
      'application/json',
    )
  }

  const response = await fetch(
    `${API_PREFIX}${path}`,
    {
      method: options.method ?? 'GET',
      headers,
      signal: options.signal,
      body: options.body === undefined
        ? undefined
        : JSON.stringify(options.body),
    },
  )

  let payload: unknown = null

  if (response.status !== 204) {
    const contentType = (
      response.headers.get('content-type')
      ?? ''
    )

    payload = contentType.includes(
      'application/json',
    )
      ? await response.json()
      : await response.text()
  }

  if (!response.ok) {
    throw new ApiError(
      getApiErrorMessage(
        payload,
        response.status,
      ),
      response.status,
      payload,
    )
  }

  return payload as T
}

export function apiGet<T>(
  path: string,
  signal?: AbortSignal,
): Promise<T> {
  return apiRequest<T>(
    path,
    {
      signal,
    },
  )
}
