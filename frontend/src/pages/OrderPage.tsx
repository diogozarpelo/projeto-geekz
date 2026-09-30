import {
  useEffect,
  useState,
} from 'react'
import {
  Link,
  useParams,
} from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import { getOrder } from '../services/orders'
import type { Order } from '../types/orders'
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

function getStatusLabel(
  labels: Record<string, string>,
  status: string,
) {
  return labels[status] ?? status
}

export function OrderPage() {
  const auth = useAuth()
  const { publicId } = useParams()

  const [order, setOrder] = useState<Order | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!auth.token || !publicId) {
      return
    }

    const currentToken = auth.token
    const currentPublicId = publicId
    const controller = new AbortController()

    async function loadOrder() {
      try {
        const response = await getOrder(
          currentToken,
          currentPublicId,
          controller.signal,
        )

        setOrder(response)
        setNotFound(false)
        setError(null)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        if (
          requestError instanceof ApiError
          && requestError.status === 404
        ) {
          setNotFound(true)
          setOrder(null)
          return
        }

        setOrder(null)
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Não foi possível carregar o pedido.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadOrder()

    return () => {
      controller.abort()
    }
  }, [auth.token, publicId])

  if (isLoading) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Pedido</p>
          <h1>Carregando pedido...</h1>
        </div>
      </section>
    )
  }

  if (notFound) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Pedido</p>
          <h1>Pedido não encontrado</h1>

          <p className="page-intro">
            Este pedido não existe ou não pertence à sua conta.
          </p>

          <Link
            className="button-primary"
            to="/catalogo"
          >
            Voltar ao catálogo
          </Link>
        </div>
      </section>
    )
  }

  if (error || !order) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Pedido</p>
          <h1>Não foi possível carregar o pedido</h1>

          <p
            className="page-intro"
            role="alert"
          >
            {error ?? 'Ocorreu um erro inesperado.'}
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="page-section">
      <div className="container checkout-success">
        <p className="eyebrow">Pedido criado</p>

        <h1>Pedido recebido</h1>

        <p className="page-intro">
          Seu pedido está registrado no sistema. O pagamento ainda não
          foi iniciado nesta etapa do projeto.
        </p>

        <div className="checkout-success__card">
          <div className="checkout-success__header">
            <div>
              <span>Número do pedido</span>
              <strong>{order.public_id}</strong>
            </div>

            <div>
              <span>Status do pedido</span>
              <strong>
                {getStatusLabel(
                  orderStatusLabels,
                  order.status,
                )}
              </strong>
            </div>

            <div>
              <span>Pagamento</span>
              <strong>
                {getStatusLabel(
                  paymentStatusLabels,
                  order.payment_status,
                )}
              </strong>
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

                  <span>
                    SKU: {item.sku}
                  </span>
                </div>

                <strong>
                  {formatCurrencyBRL(item.total_price)}
                </strong>
              </div>
            ))}
          </div>

          <div className="checkout-success__items">
            <div className="checkout-success__item">
              <div>
                <strong>Cliente</strong>

                <span>{order.customer_name}</span>
                <span>{order.customer_email}</span>
              </div>
            </div>

            <div className="checkout-success__item">
              <div>
                <strong>Entrega</strong>

                <span>
                  {order.shipping_street}
                  {', '}
                  {order.shipping_number}
                </span>

                {order.shipping_complement && (
                  <span>
                    {order.shipping_complement}
                  </span>
                )}

                <span>
                  {order.shipping_neighborhood}
                  {' · '}
                  {order.shipping_city}
                  {' / '}
                  {order.shipping_state}
                </span>

                <span>
                  CEP: {order.shipping_postal_code}
                </span>
              </div>
            </div>
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
            Continuar comprando
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
