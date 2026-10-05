import {
  useState,
  type FormEvent,
} from 'react'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'


export function MyAccountPage() {
  const auth = useAuth()

  const [firstName, setFirstName] = useState(
    auth.user?.first_name ?? '',
  )
  const [lastName, setLastName] = useState(
    auth.user?.last_name ?? '',
  )
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    try {
      setIsSubmitting(true)
      setError(null)
      setSuccess(null)

      const updatedUser = await auth.updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      })

      setFirstName(updatedUser.first_name)
      setLastName(updatedUser.last_name)
      setSuccess('Dados da conta atualizados com sucesso.')
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível atualizar sua conta agora.',
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
          <h1>Minha conta</h1>

          <p className="page-intro">
            Consulte seus dados e mantenha seu nome atualizado.
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
                aria-describedby="account-email-help"
                readOnly
                type="email"
                value={auth.user?.email ?? ''}
              />

              <span
                className="account-form__note"
                id="account-email-help"
              >
                O e-mail da conta não pode ser alterado aqui.
              </span>
            </label>

            {error && (
              <p
                className="auth-form__error"
                role="alert"
              >
                {error}
              </p>
            )}

            {success && (
              <p
                className="account-form__success"
                role="status"
              >
                {success}
              </p>
            )}

            <button
              className="button-primary"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting
                ? 'Salvando...'
                : 'Salvar alterações'}
            </button>
          </form>
        </div>
      </div>
    </section>
  )
}
