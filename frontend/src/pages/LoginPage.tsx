import {
  useState,
  type FormEvent,
} from 'react'
import {
  Link,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'

type LoginLocationState = {
  from?: string
}

export function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    try {
      setIsSubmitting(true)
      setError(null)

      await auth.signIn({
        email,
        password,
      })

      const state = (
        location.state as LoginLocationState | null
      )

      navigate(
        state?.from ?? '/catalogo',
        {
          replace: true,
        },
      )
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível entrar agora.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="page-section">
      <div className="container auth-page">
        <div className="auth-card">
          <p className="eyebrow">Conta</p>
          <h1>Entrar</h1>

          <p className="page-intro">
            Entre para acessar seu carrinho e finalizar pedidos.
          </p>

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <label>
              E-mail
              <input
                autoComplete="email"
                required
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value)
                }}
              />
            </label>

            <label>
              Senha
              <input
                autoComplete="current-password"
                required
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value)
                }}
              />
            </label>

            {error && (
              <p
                className="auth-form__error"
                role="alert"
              >
                {error}
              </p>
            )}

            <button
              className="button-primary"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting
                ? 'Entrando...'
                : 'Entrar'}
            </button>
          </form>

          <p className="auth-card__footer">
            Ainda não tem conta?{' '}
            <Link to="/cadastro">
              Criar conta
            </Link>
          </p>
        </div>
      </div>
    </section>
  )
}
