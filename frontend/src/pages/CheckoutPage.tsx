import {
  useEffect,
  useState,
  type FormEvent,
} from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import { getCurrentUserAddress } from '../services/auth'
import { getActiveCart } from '../services/cart'
import { createOrderFromCart } from '../services/orders'
import type { Cart } from '../types/cart'
import type { Order } from '../types/orders'
import { formatCurrencyBRL } from '../utils/currency'

export function CheckoutPage() {
  const auth = useAuth()
  const navigate = useNavigate()

  const defaultName = [
    auth.user?.first_name,
    auth.user?.last_name,
  ]
    .filter(Boolean)
    .join(' ')

  const [cart, setCart] = useState<Cart | null>(null)
  const [order, setOrder] = useState<Order | null>(null)

  const [customerName, setCustomerName] = useState(defaultName)
  const [customerEmail, setCustomerEmail] = useState(
    auth.user?.email ?? '',
  )

  const [postalCode, setPostalCode] = useState('')
  const [street, setStreet] = useState('')
  const [number, setNumber] = useState('')
  const [complement, setComplement] = useState('')
  const [neighborhood, setNeighborhood] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [hasSavedAddress, setHasSavedAddress] = useState(false)
  const [notes, setNotes] = useState('')

  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!auth.token) {
      return
    }

    const currentToken = auth.token
    const controller = new AbortController()

    async function loadCheckout() {
      try {
        const [
          cartResult,
          addressResult,
        ] = await Promise.allSettled([
          getActiveCart(
            currentToken,
            controller.signal,
          ),
          getCurrentUserAddress(
            currentToken,
            controller.signal,
          ),
        ])

        if (controller.signal.aborted) {
          return
        }

        if (cartResult.status === 'rejected') {
          throw cartResult.reason
        }

        setCart(cartResult.value)

        if (
          addressResult.status === 'fulfilled'
          && addressResult.value.address
        ) {
          const address = addressResult.value.address

          setPostalCode(address.postal_code)
          setStreet(address.street)
          setNumber(address.number)
          setComplement(address.complement)
          setNeighborhood(address.neighborhood)
          setCity(address.city)
          setState(address.state)
          setHasSavedAddress(true)
        }

        setError(null)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Não foi possível carregar o checkout.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadCheckout()

    return () => {
      controller.abort()
    }
  }, [auth.token])

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (
      !auth.token
      || !cart
      || cart.items.length === 0
    ) {
      return
    }

    const currentToken = auth.token

    try {
      setIsSubmitting(true)
      setError(null)

      const response = await createOrderFromCart(
        currentToken,
        {
          cart_public_id: cart.public_id,
          customer_name: customerName.trim(),
          customer_email: customerEmail.trim(),
          shipping_postal_code: postalCode.trim(),
          shipping_street: street.trim(),
          shipping_number: number.trim(),
          shipping_complement: complement.trim(),
          shipping_neighborhood: neighborhood.trim(),
          shipping_city: city.trim(),
          shipping_state: state.trim().toUpperCase(),
          shipping_country: 'BR',
          notes: notes.trim(),
        },
      )

      setOrder(response)

      navigate(
        `/pedidos/${response.public_id}`,
        {
          replace: true,
        },
      )
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível finalizar o pedido.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Checkout</p>
          <h1>Carregando checkout...</h1>
        </div>
      </section>
    )
  }

  if (order) {
    return (
      <section className="page-section">
        <div className="container checkout-success">
          <p className="eyebrow">Pedido criado</p>

          <h1>Pedido recebido</h1>

          <p className="page-intro">
            Seu pedido foi criado com sucesso. O pagamento ainda não
            foi iniciado nesta etapa do projeto.
          </p>

          <div className="checkout-success__card">
            <div className="checkout-success__header">
              <div>
                <span>Número do pedido</span>
                <strong>{order.public_id}</strong>
              </div>

              <div>
                <span>Status</span>
                <strong>{order.status}</strong>
              </div>
            </div>

            <div className="checkout-success__items">
              {order.items.map((item) => (
                <div
                  className="checkout-success__item"
                  key={item.id}
                >
                  <div>
                    <strong>{item.product_name}</strong>

                    <span>
                      {item.color_name}
                      {' · '}
                      {item.size_name}
                      {' · '}
                      {item.quantity}
                      {' unidade(s)'}
                    </span>
                  </div>

                  <strong>
                    {formatCurrencyBRL(item.total_price)}
                  </strong>
                </div>
              ))}
            </div>

            <div className="checkout-success__total">
              <span>Total</span>

              <strong>
                {formatCurrencyBRL(order.total_amount)}
              </strong>
            </div>
          </div>

          <div className="checkout-success__actions">
            <Link
              className="button-primary"
              to="/catalogo"
            >
              Voltar ao catálogo
            </Link>

            <Link
              className="button-secondary"
              to="/carrinho"
            >
              Ver novo carrinho
            </Link>
          </div>
        </div>
      </section>
    )
  }

  if (!cart) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Checkout</p>
          <h1>Não foi possível abrir o checkout</h1>

          {error && (
            <p
              className="page-intro"
              role="alert"
            >
              {error}
            </p>
          )}
        </div>
      </section>
    )
  }

  if (cart.items.length === 0) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Checkout</p>
          <h1>Seu carrinho está vazio</h1>

          <p className="page-intro">
            Adicione pelo menos um produto antes de finalizar o pedido.
          </p>

          <Link
            className="button-primary"
            to="/catalogo"
          >
            Ver catálogo
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Checkout</p>
        <h1>Finalizar pedido</h1>

        <p className="page-intro">
          Confira seus dados e o endereço de entrega antes de criar o pedido.
        </p>

        {error && (
          <p
            className="checkout-feedback"
            role="alert"
          >
            {error}
          </p>
        )}

        <div className="checkout-layout">
          <form
            className="checkout-form"
            onSubmit={handleSubmit}
          >
            <section className="checkout-form__section">
              <div className="checkout-form__heading">
                <span>01</span>

                <div>
                  <h2>Dados do cliente</h2>
                  <p>
                    Informações que ficarão registradas no pedido.
                  </p>
                </div>
              </div>

              <div className="checkout-form__fields">
                <label>
                  Nome completo
                  <input
                    required
                    autoComplete="name"
                    maxLength={160}
                    type="text"
                    value={customerName}
                    onChange={(event) => {
                      setCustomerName(event.target.value)
                    }}
                  />
                </label>

                <label>
                  E-mail
                  <input
                    required
                    autoComplete="email"
                    type="email"
                    value={customerEmail}
                    onChange={(event) => {
                      setCustomerEmail(event.target.value)
                    }}
                  />
                </label>
              </div>
            </section>

            <section className="checkout-form__section">
              <div className="checkout-form__heading">
                <span>02</span>

                <div>
                  <h2>Endereço de entrega</h2>
                  <p>
                    {hasSavedAddress
                      ? 'Seu endereço padrão foi carregado. Você pode alterá-lo para este pedido.'
                      : 'Preencha o endereço que será associado ao pedido.'}
                  </p>
                </div>
              </div>

              <div className="checkout-form__fields">
                <div className="checkout-form__row">
                  <label>
                    CEP
                    <input
                      required
                      autoComplete="postal-code"
                      maxLength={20}
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
                      required
                      autoComplete="address-level1"
                      maxLength={80}
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
                    required
                    autoComplete="address-line1"
                    maxLength={180}
                    type="text"
                    value={street}
                    onChange={(event) => {
                      setStreet(event.target.value)
                    }}
                  />
                </label>

                <div className="checkout-form__row">
                  <label>
                    Número
                    <input
                      required
                      maxLength={30}
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

                <div className="checkout-form__row">
                  <label>
                    Bairro
                    <input
                      required
                      maxLength={120}
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
                      required
                      autoComplete="address-level2"
                      maxLength={120}
                      type="text"
                      value={city}
                      onChange={(event) => {
                        setCity(event.target.value)
                      }}
                    />
                  </label>
                </div>
              </div>
            </section>

            <section className="checkout-form__section">
              <div className="checkout-form__heading">
                <span>03</span>

                <div>
                  <h2>Observações</h2>
                  <p>
                    Campo opcional para informações adicionais.
                  </p>
                </div>
              </div>

              <label>
                Observações do pedido
                <textarea
                  rows={5}
                  value={notes}
                  onChange={(event) => {
                    setNotes(event.target.value)
                  }}
                />
              </label>
            </section>

            <button
              className="button-primary checkout-form__submit"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting
                ? 'Criando pedido...'
                : 'Criar pedido'}
            </button>
          </form>

          <aside className="checkout-summary">
            <p className="eyebrow">Resumo</p>
            <h2>Seu pedido</h2>

            <div className="checkout-summary__items">
              {cart.items.map((item) => (
                <div
                  className="checkout-summary__item"
                  key={item.id}
                >
                  <div>
                    <strong>{item.product_name}</strong>

                    <span>
                      {item.color_name}
                      {' · '}
                      {item.size_name}
                      {' · '}
                      {item.quantity}
                      {'x'}
                    </span>
                  </div>

                  <strong>
                    {formatCurrencyBRL(item.total_price)}
                  </strong>
                </div>
              ))}
            </div>

            <div className="checkout-summary__row">
              <span>Itens</span>
              <strong>{cart.total_items}</strong>
            </div>

            <div className="checkout-summary__row checkout-summary__total">
              <span>Total</span>

              <strong>
                {formatCurrencyBRL(cart.subtotal)}
              </strong>
            </div>

            <p className="checkout-summary__note">
              Nesta etapa, frete e desconto permanecem em R$ 0,00 e
              nenhum pagamento externo será iniciado.
            </p>

            <Link
              className="checkout-summary__back"
              to="/carrinho"
            >
              Voltar ao carrinho
            </Link>
          </aside>
        </div>
      </div>
    </section>
  )
}
