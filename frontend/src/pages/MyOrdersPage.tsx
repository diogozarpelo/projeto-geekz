import {
  useEffect,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import { getOrders } from '../services/orders'
import type { PaginatedOrders } from '../types/orders'
import { formatCurrencyBRL } from '../utils/currency'

const orderStatusLabels: Record<string, string> = {
  pending: 'Pendente',
  confirmed: 'Confirmado',
  processing: 'Em processamento',
  shipped: 'Enviado',
  delivered: 'Entregue',
  cancelled: 'Cancelado',
}

const paymentStatusLabels: Record<string, string> = {
  pending: 'Pendente',
  paid: 'Pago',
  failed: 'Falhou',
  refunded: 'Reembolsado',
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(
    'pt-BR',
    {
      dateStyle: 'short',
      timeStyle: 'short',
    },
  ).format(new Date(value))
}

export function MyOrdersPage() {
  const auth = useAuth()

  const [page, setPage] = useState(1)
  const [orders, setOrders] = useState<PaginatedOrders | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!auth.token) {
      return
    }

    const currentToken = auth.token
    const controller = new AbortController()

    async function loadOrders() {
      try {
        setIsLoading(true)

        const response = await getOrders(
          currentToken,
          page,
          controller.signal,
        )

        setOrders(response)
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
            : 'Não foi possível carregar seus pedidos.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadOrders()

    return () => {
      controller.abort()
    }
  }, [auth.token, page])

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Conta</p>
        <h1>Meus pedidos</h1>

        <p className="page-intro">
          Consulte os pedidos vinculados à sua conta e abra os detalhes
          de cada compra.
        </p>

        {error && (
          <p
            className="orders-feedback"
            role="alert"
          >
            {error}
          </p>
        )}

        {isLoading ? (
          <p className="orders-status">
            Carregando pedidos...
          </p>
        ) : orders && orders.results.length > 0 ? (
          <>
            <div className="orders-list">
              {orders.results.map((order) => (
                <article
                  className="order-card"
                  key={order.public_id}
                >
                  <div className="order-card__header">
                    <div>
                      <span>Pedido</span>

                      <strong>
                        {order.public_id}
                      </strong>
                    </div>

                    <strong className="order-card__total">
                      {formatCurrencyBRL(order.total_amount)}
                    </strong>
                  </div>

                  <div className="order-card__meta">
                    <div>
                      <span>Data</span>
                      <strong>{formatDate(order.created_at)}</strong>
                    </div>

                    <div>
                      <span>Status</span>
                      <strong>
                        {orderStatusLabels[order.status] ?? order.status}
                      </strong>
                    </div>

                    <div>
                      <span>Pagamento</span>
                      <strong>
                        {paymentStatusLabels[order.payment_status]
                          ?? order.payment_status}
                      </strong>
                    </div>

                    <div>
                      <span>Itens</span>
                      <strong>
                        {order.items.reduce(
                          (total, item) => total + item.quantity,
                          0,
                        )}
                      </strong>
                    </div>
                  </div>

                  <div className="order-card__footer">
                    <span>
                      {order.items
                        .map((item) => item.product_name)
                        .join(', ')}
                    </span>

                    <Link
                      className="button-secondary"
                      to={`/pedidos/${order.public_id}`}
                    >
                      Ver pedido
                    </Link>
                  </div>
                </article>
              ))}
            </div>

            <div className="orders-pagination">
              <button
                className="button-secondary"
                disabled={!orders.previous}
                type="button"
                onClick={() => {
                  setPage((currentPage) => (
                    Math.max(1, currentPage - 1)
                  ))
                }}
              >
                Anterior
              </button>

              <span>
                Página {page}
                {' · '}
                {orders.count} pedido(s)
              </span>

              <button
                className="button-secondary"
                disabled={!orders.next}
                type="button"
                onClick={() => {
                  setPage((currentPage) => currentPage + 1)
                }}
              >
                Próxima
              </button>
            </div>
          </>
        ) : (
          <div className="orders-empty">
            <h2>Você ainda não possui pedidos</h2>

            <p>
              Quando você finalizar uma compra, ela aparecerá aqui.
            </p>

            <Link
              className="button-primary"
              to="/catalogo"
            >
              Ver catálogo
            </Link>
          </div>
        )}
      </div>
    </section>
  )
}
