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

  const [profileError, setProfileError] =
    useState<string | null>(null)
  const [profileSuccess, setProfileSuccess] =
    useState<string | null>(null)
  const [isSavingProfile, setIsSavingProfile] =
    useState(false)

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] =
    useState('')

  const [passwordError, setPasswordError] =
    useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] =
    useState<string | null>(null)
  const [isChangingPassword, setIsChangingPassword] =
    useState(false)

  async function handleProfileSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    try {
      setIsSavingProfile(true)
      setProfileError(null)
      setProfileSuccess(null)

      const updatedUser = await auth.updateProfile({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      })

      setFirstName(updatedUser.first_name)
      setLastName(updatedUser.last_name)
      setProfileSuccess(
        'Dados da conta atualizados com sucesso.',
      )
    } catch (requestError) {
      setProfileError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível atualizar sua conta agora.',
      )
    } finally {
      setIsSavingProfile(false)
    }
  }

  async function handlePasswordSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (newPassword !== newPasswordConfirm) {
      setPasswordError(
        'A confirmação da nova senha não confere.',
      )
      setPasswordSuccess(null)
      return
    }

    try {
      setIsChangingPassword(true)
      setPasswordError(null)
      setPasswordSuccess(null)

      await auth.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      })

      setCurrentPassword('')
      setNewPassword('')
      setNewPasswordConfirm('')

      setPasswordSuccess(
        'Senha alterada com sucesso.',
      )
    } catch (requestError) {
      setPasswordError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível alterar sua senha agora.',
      )
    } finally {
      setIsChangingPassword(false)
    }
  }

  return (
    <section className="page-section">
      <div className="container auth-page">
        <div className="auth-card">
          <p className="eyebrow">Conta</p>
          <h1>Minha conta</h1>

          <p className="page-intro">
            Consulte seus dados e mantenha sua conta atualizada.
          </p>

          <section
            className="account-section"
            aria-labelledby="account-profile-title"
          >
            <h2 id="account-profile-title">
              Dados pessoais
            </h2>

            <form
              className="auth-form"
              onSubmit={handleProfileSubmit}
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

              {profileError && (
                <p
                  className="auth-form__error"
                  role="alert"
                >
                  {profileError}
                </p>
              )}

              {profileSuccess && (
                <p
                  className="account-form__success"
                  role="status"
                >
                  {profileSuccess}
                </p>
              )}

              <button
                className="button-primary"
                disabled={isSavingProfile}
                type="submit"
              >
                {isSavingProfile
                  ? 'Salvando...'
                  : 'Salvar alterações'}
              </button>
            </form>
          </section>

          <section
            className="account-section account-section--password"
            aria-labelledby="account-password-title"
          >
            <h2 id="account-password-title">
              Alterar senha
            </h2>

            <p className="account-section__intro">
              Informe sua senha atual e escolha uma nova senha.
            </p>

            <form
              className="auth-form"
              onSubmit={handlePasswordSubmit}
            >
              <label>
                Senha atual
                <input
                  autoComplete="current-password"
                  required
                  type="password"
                  value={currentPassword}
                  onChange={(event) => {
                    setCurrentPassword(event.target.value)
                  }}
                />
              </label>

              <label>
                Nova senha
                <input
                  autoComplete="new-password"
                  required
                  type="password"
                  value={newPassword}
                  onChange={(event) => {
                    setNewPassword(event.target.value)
                  }}
                />
              </label>

              <label>
                Confirmar nova senha
                <input
                  autoComplete="new-password"
                  required
                  type="password"
                  value={newPasswordConfirm}
                  onChange={(event) => {
                    setNewPasswordConfirm(event.target.value)
                  }}
                />
              </label>

              {passwordError && (
                <p
                  className="auth-form__error"
                  role="alert"
                >
                  {passwordError}
                </p>
              )}

              {passwordSuccess && (
                <p
                  className="account-form__success"
                  role="status"
                >
                  {passwordSuccess}
                </p>
              )}

              <button
                className="button-primary"
                disabled={isChangingPassword}
                type="submit"
              >
                {isChangingPassword
                  ? 'Alterando senha...'
                  : 'Alterar senha'}
              </button>
            </form>
          </section>
        </div>
      </div>
    </section>
  )
}
