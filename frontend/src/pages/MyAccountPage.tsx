import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import {
  getCurrentUserAddress,
  updateCurrentUserAddress,
} from '../services/auth'


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

  const [postalCode, setPostalCode] = useState('')
  const [street, setStreet] = useState('')
  const [number, setNumber] = useState('')
  const [complement, setComplement] = useState('')
  const [neighborhood, setNeighborhood] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')

  const [addressError, setAddressError] =
    useState<string | null>(null)
  const [addressSuccess, setAddressSuccess] =
    useState<string | null>(null)
  const [isLoadingAddress, setIsLoadingAddress] =
    useState(() => Boolean(auth.token))
  const [isSavingAddress, setIsSavingAddress] =
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

  useEffect(() => {
    if (!auth.token) {
      return
    }

    const currentToken = auth.token
    const controller = new AbortController()

    async function loadAddress() {
      try {
        const response = await getCurrentUserAddress(
          currentToken,
          controller.signal,
        )

        if (!response.address) {
          return
        }

        setPostalCode(response.address.postal_code)
        setStreet(response.address.street)
        setNumber(response.address.number)
        setComplement(response.address.complement)
        setNeighborhood(response.address.neighborhood)
        setCity(response.address.city)
        setState(response.address.state)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setAddressError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Não foi possível carregar seu endereço.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingAddress(false)
        }
      }
    }

    void loadAddress()

    return () => {
      controller.abort()
    }
  }, [auth.token])

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

  async function handleAddressSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (!auth.token) {
      return
    }

    try {
      setIsSavingAddress(true)
      setAddressError(null)
      setAddressSuccess(null)

      const response = await updateCurrentUserAddress(
        auth.token,
        {
          postal_code: postalCode.trim(),
          street: street.trim(),
          number: number.trim(),
          complement: complement.trim(),
          neighborhood: neighborhood.trim(),
          city: city.trim(),
          state: state.trim().toUpperCase(),
          country: 'BR',
        },
      )

      if (response.address) {
        setPostalCode(response.address.postal_code)
        setStreet(response.address.street)
        setNumber(response.address.number)
        setComplement(response.address.complement)
        setNeighborhood(response.address.neighborhood)
        setCity(response.address.city)
        setState(response.address.state)
      }

      setAddressSuccess(
        'Endereço padrão salvo com sucesso.',
      )
    } catch (requestError) {
      setAddressError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível salvar seu endereço agora.',
      )
    } finally {
      setIsSavingAddress(false)
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
            className="account-section"
            aria-labelledby="account-address-title"
          >
            <h2 id="account-address-title">
              Endereço padrão
            </h2>

            <p className="account-section__intro">
              Salve seu endereço principal de entrega para reutilizá-lo
              em seus próximos pedidos.
            </p>

            {isLoadingAddress ? (
              <p className="account-form__note">
                Carregando endereço...
              </p>
            ) : (
              <form
                className="auth-form"
                onSubmit={handleAddressSubmit}
              >
                <div className="auth-form__row">
                  <label>
                    CEP
                    <input
                      autoComplete="postal-code"
                      maxLength={20}
                      required
                      type="text"
                      value={postalCode}
                      onChange={(event) => {
                        setPostalCode(event.target.value)
                      }}
                    />
                  </label>

                  <label>
                    Estado
                    <input
                      autoComplete="address-level1"
                      maxLength={80}
                      required
                      type="text"
                      value={state}
                      onChange={(event) => {
                        setState(event.target.value)
                      }}
                    />
                  </label>
                </div>

                <label>
                  Rua
                  <input
                    autoComplete="address-line1"
                    maxLength={180}
                    required
                    type="text"
                    value={street}
                    onChange={(event) => {
                      setStreet(event.target.value)
                    }}
                  />
                </label>

                <div className="auth-form__row">
                  <label>
                    Número
                    <input
                      maxLength={30}
                      required
                      type="text"
                      value={number}
                      onChange={(event) => {
                        setNumber(event.target.value)
                      }}
                    />
                  </label>

                  <label>
                    Complemento
                    <input
                      autoComplete="address-line2"
                      maxLength={120}
                      type="text"
                      value={complement}
                      onChange={(event) => {
                        setComplement(event.target.value)
                      }}
                    />
                  </label>
                </div>

                <div className="auth-form__row">
                  <label>
                    Bairro
                    <input
                      maxLength={120}
                      required
                      type="text"
                      value={neighborhood}
                      onChange={(event) => {
                        setNeighborhood(event.target.value)
                      }}
                    />
                  </label>

                  <label>
                    Cidade
                    <input
                      autoComplete="address-level2"
                      maxLength={120}
                      required
                      type="text"
                      value={city}
                      onChange={(event) => {
                        setCity(event.target.value)
                      }}
                    />
                  </label>
                </div>

                {addressError && (
                  <p
                    className="auth-form__error"
                    role="alert"
                  >
                    {addressError}
                  </p>
                )}

                {addressSuccess && (
                  <p
                    className="account-form__success"
                    role="status"
                  >
                    {addressSuccess}
                  </p>
                )}

                <button
                  className="button-primary"
                  disabled={isSavingAddress}
                  type="submit"
                >
                  {isSavingAddress
                    ? 'Salvando endereço...'
                    : 'Salvar endereço'}
                </button>
              </form>
            )}
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
