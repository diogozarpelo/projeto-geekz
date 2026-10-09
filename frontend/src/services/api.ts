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

type ApiMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

type ApiRequestOptions = {
  method?: ApiMethod
  signal?: AbortSignal
  token?: string | null
  body?: unknown
}

const API_ERROR_FIELD_LABELS: Record<string, string> = {
  email: 'E-mail',
  password: 'Senha',
  password_confirm: 'Confirmação de senha',
  current_password: 'Senha atual',
  new_password: 'Nova senha',
  new_password_confirm: 'Confirmação da nova senha',
  first_name: 'Nome',
  last_name: 'Sobrenome',
  customer_name: 'Nome completo',
  customer_email: 'E-mail',
  postal_code: 'CEP',
  street: 'Rua',
  number: 'Número',
  complement: 'Complemento',
  neighborhood: 'Bairro',
  city: 'Cidade',
  state: 'Estado',
  country: 'País',
  shipping_postal_code: 'CEP',
  shipping_street: 'Rua',
  shipping_number: 'Número',
  shipping_complement: 'Complemento',
  shipping_neighborhood: 'Bairro',
  shipping_city: 'Cidade',
  shipping_state: 'Estado',
  shipping_country: 'País',
  cart_public_id: 'Carrinho',
  notes: 'Observações',
}

const API_ERROR_MESSAGE_TRANSLATIONS: Record<string, string> = {
  'This field is required.': 'Este campo é obrigatório.',
  'This field may not be blank.': 'Este campo não pode ficar vazio.',
  'This field may not be null.': 'Este campo não pode ser nulo.',
  'Enter a valid email address.': 'Informe um e-mail válido.',
  'Not a valid string.': 'Valor de texto inválido.',
  'Must be a valid boolean.': 'Valor booleano inválido.',
  'Current password is incorrect.': 'A senha atual está incorreta.',
  'Password confirmation does not match.': 'A confirmação da senha não confere.',
  'Invalid email or password.': 'E-mail ou senha inválidos.',
  'This account is inactive.': 'Esta conta está inativa.',
  'A user with this email already exists.': 'Já existe uma conta com este e-mail.',
}

function translateApiErrorMessage(
  message: string,
) {
  return API_ERROR_MESSAGE_TRANSLATIONS[message]
    ?? message
}

function collectApiErrorMessages(
  value: unknown,
  fieldName?: string,
): string[] {
  if (typeof value === 'string') {
    const message = translateApiErrorMessage(
      value.trim(),
    )

    if (!message) {
      return []
    }

    if (
      !fieldName
      || fieldName === 'detail'
      || fieldName === 'non_field_errors'
    ) {
      return [message]
    }

    const label = API_ERROR_FIELD_LABELS[fieldName]
      ?? fieldName.replaceAll('_', ' ')

    return [`${label}: ${message}`]
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => (
      collectApiErrorMessages(
        item,
        fieldName,
      )
    ))
  }

  if (
    typeof value === 'object'
    && value !== null
  ) {
    return Object.entries(value).flatMap(
      ([key, nestedValue]) => (
        collectApiErrorMessages(
          nestedValue,
          key,
        )
      ),
    )
  }

  return []
}

function getApiErrorMessage(
  payload: unknown,
  status: number,
) {
  const messages = collectApiErrorMessages(
    payload,
  )

  if (messages.length > 0) {
    return [...new Set(messages)].join(' ')
  }

  return `Não foi possível concluir a solicitação. Código ${status}.`
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
