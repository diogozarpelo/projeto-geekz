import {
  useState,
  type FormEvent,
} from 'react'
import {
  Link,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'

export function RegisterPage() {
  const auth = useAuth()
  const navigate = useNavigate()

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (password !== passwordConfirm) {
      setError('As senhas precisam ser iguais.')
      return
    }

    try {
      setIsSubmitting(true)
      setError(null)

      await auth.signUp({
        email,
        first_name: firstName,
        last_name: lastName,
        password,
        password_confirm: passwordConfirm,
      })

      navigate(
        '/catalogo',
        {
          replace: true,
        },
      )
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível criar a conta agora.',
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
          <h1>Criar conta</h1>

          <p className="page-intro">
            Crie sua conta para usar o carrinho e acompanhar pedidos.
          </p>

          <form
            className="auth-form"
            onSubmit={handleSubmit}
          >
            <div className="auth-form__row">
              <label>
                Nome
                <input
                  autoComplete="given-name"
                  type="text"
                  value={firstName}
                  onChange={(event) => {
                    setFirstName(event.target.value)
                  }}
                />
              </label>

              <label>
                Sobrenome
                <input
                  autoComplete="family-name"
                  type="text"
                  value={lastName}
                  onChange={(event) => {
                    setLastName(event.target.value)
                  }}
                />
              </label>
            </div>

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
                autoComplete="new-password"
                required
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value)
                }}
              />
            </label>

            <label>
              Confirmar senha
              <input
                autoComplete="new-password"
                required
                type="password"
                value={passwordConfirm}
                onChange={(event) => {
                  setPasswordConfirm(event.target.value)
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
                ? 'Criando conta...'
                : 'Criar conta'}
            </button>
          </form>

          <p className="auth-card__footer">
            Já tem conta?{' '}
            <Link to="/login">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </section>
  )
}
