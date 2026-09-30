import {
  useEffect,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import {
  getActiveCart,
  removeCartItem,
  updateCartItem,
} from '../services/cart'
import type {
  Cart,
  CartItem,
} from '../types/cart'
import { formatCurrencyBRL } from '../utils/currency'

export function CartPage() {
  const auth = useAuth()

  const [cart, setCart] = useState<Cart | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [busyItemId, setBusyItemId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!auth.token) {
      return
    }

    const currentToken = auth.token
    const controller = new AbortController()

    async function loadCart() {
      try {
        const response = await getActiveCart(
          currentToken,
          controller.signal,
        )

        setCart(response)
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
            : 'Não foi possível carregar o carrinho.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadCart()

    return () => {
      controller.abort()
    }
  }, [auth.token])

  async function changeQuantity(
    item: CartItem,
    quantity: number,
  ) {
    const currentToken = auth.token

    if (
      !currentToken
      || quantity < 1
      || quantity > item.available_stock
    ) {
      return
    }

    try {
      setBusyItemId(item.id)
      setError(null)

      const response = await updateCartItem(
        currentToken,
        item.id,
        {
          quantity,
        },
      )

      setCart(response)
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível atualizar o item.',
      )
    } finally {
      setBusyItemId(null)
    }
  }

  async function removeItem(itemId: number) {
    const currentToken = auth.token

    if (!currentToken) {
      return
    }

    try {
      setBusyItemId(itemId)
      setError(null)

      const response = await removeCartItem(
        currentToken,
        itemId,
      )

      setCart(response)
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível remover o item.',
      )
    } finally {
      setBusyItemId(null)
    }
  }

  if (isLoading) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Carrinho</p>
          <h1>Carregando carrinho...</h1>
        </div>
      </section>
    )
  }

  if (!cart) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Carrinho</p>
          <h1>Não foi possível abrir seu carrinho</h1>

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

  const isEmpty = cart.items.length === 0

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Carrinho</p>
        <h1>Seu carrinho</h1>

        <p className="page-intro">
          Revise seus produtos antes de seguir para a finalização.
        </p>

        {error && (
          <p
            className="cart-feedback"
            role="alert"
          >
            {error}
          </p>
        )}

        {isEmpty ? (
          <div className="cart-empty">
            <h2>Seu carrinho está vazio</h2>

            <p>
              Escolha uma camiseta no catálogo para começar seu pedido.
            </p>

            <Link
              className="button-primary"
              to="/catalogo"
            >
              Ver catálogo
            </Link>
          </div>
        ) : (
          <div className="cart-layout">
            <div className="cart-items">
              {cart.items.map((item) => {
                const isBusy = busyItemId === item.id
                const canDecrease = item.quantity > 1
                const canIncrease = (
                  item.is_in_stock
                  && item.quantity < item.available_stock
                )

                return (
                  <article
                    className="cart-item"
                    key={item.id}
                  >
                    <div className="cart-item__placeholder">
                      Geekz
                    </div>

                    <div className="cart-item__content">
                      <div className="cart-item__header">
                        <div>
                          <Link
                            className="cart-item__name"
                            to={`/produto/${item.product_slug}`}
                          >
                            {item.product_name}
                          </Link>

                          <p className="cart-item__variant">
                            {item.color_name}
                            {' · '}
                            {item.size_name}
                          </p>

                          <p className="cart-item__sku">
                            SKU: {item.sku}
                          </p>
                        </div>

                        <strong className="cart-item__total">
                          {formatCurrencyBRL(item.total_price)}
                        </strong>
                      </div>

                      <div className="cart-item__footer">
                        <div
                          className="cart-quantity"
                          aria-label={`Quantidade de ${item.product_name}`}
                        >
                          <button
                            type="button"
                            disabled={!canDecrease || isBusy}
                            aria-label="Diminuir quantidade"
                            onClick={() => {
                              void changeQuantity(
                                item,
                                item.quantity - 1,
                              )
                            }}
                          >
                            −
                          </button>

                          <span>
                            {item.quantity}
                          </span>

                          <button
                            type="button"
                            disabled={!canIncrease || isBusy}
                            aria-label="Aumentar quantidade"
                            onClick={() => {
                              void changeQuantity(
                                item,
                                item.quantity + 1,
                              )
                            }}
                          >
                            +
                          </button>
                        </div>

                        <span className="cart-item__unit-price">
                          {formatCurrencyBRL(item.unit_price)}
                          {' por unidade'}
                        </span>

                        <button
                          className="cart-item__remove"
                          type="button"
                          disabled={isBusy}
                          onClick={() => {
                            void removeItem(item.id)
                          }}
                        >
                          Remover
                        </button>
                      </div>

                      <p className="cart-item__stock">
                        {item.available_stock}
                        {' unidade(s) disponível(is)'}
                      </p>
                    </div>
                  </article>
                )
              })}
            </div>

            <aside className="cart-summary">
              <p className="eyebrow">
                Resumo
              </p>

              <h2>
                Pedido
              </h2>

              <div className="cart-summary__row">
                <span>Itens</span>
                <strong>{cart.total_items}</strong>
              </div>

              <div className="cart-summary__row cart-summary__total">
                <span>Subtotal</span>
                <strong>
                  {formatCurrencyBRL(cart.subtotal)}
                </strong>
              </div>

              <p className="cart-summary__note">
                Frete e demais informações serão definidos no checkout.
              </p>

              <Link
                className="button-primary cart-summary__checkout"
                to="/checkout"
              >
                Ir para o checkout
              </Link>

              <Link
                className="cart-summary__continue"
                to="/catalogo"
              >
                Continuar comprando
              </Link>
            </aside>
          </div>
        )}
      </div>
    </section>
  )
}
