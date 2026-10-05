import {
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  Link,
  useParams,
} from 'react-router-dom'

import { useAuth } from '../auth/useAuth'
import { ApiError } from '../services/api'
import {
  cancelOrder,
  createPixPayment,
  getOrder,
  getPaymentCapabilities,
} from '../services/orders'
import type {
  Order,
  Payment,
  PaymentCapabilities,
} from '../types/orders'
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
  cancelled: 'Cancelado',
  refunded: 'Reembolsado',
}

function getStatusLabel(
  labels: Record<string, string>,
  status: string,
) {
  return labels[status] ?? status
}

function getStringProviderData(
  payment: Payment | undefined,
  key: string,
) {
  const value = payment?.provider_data[key]

  return typeof value === 'string'
    ? value.trim()
    : ''
}

export function OrderPage() {
  const auth = useAuth()
  const { publicId } = useParams()

  const [order, setOrder] = useState<Order | null>(null)
  const [capabilities, setCapabilities] =
    useState<PaymentCapabilities | null>(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingCapabilities, setIsLoadingCapabilities] =
    useState(true)
  const [isCreatingPix, setIsCreatingPix] = useState(false)
  const [isCancellingOrder, setIsCancellingOrder] = useState(false)

  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capabilitiesError, setCapabilitiesError] =
    useState<string | null>(null)
  const [paymentError, setPaymentError] =
    useState<string | null>(null)
  const [cancelError, setCancelError] =
    useState<string | null>(null)
  const [pixCopied, setPixCopied] = useState(false)

  useEffect(() => {
    if (!auth.token || !publicId) {
      return
    }

    const currentToken = auth.token
    const currentPublicId = publicId
    const controller = new AbortController()

    async function loadOrder() {
      try {
        setIsLoading(true)

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

  useEffect(() => {
    if (!auth.token) {
      return
    }

    const currentToken = auth.token
    const controller = new AbortController()

    async function loadCapabilities() {
      try {
        setIsLoadingCapabilities(true)

        const response = await getPaymentCapabilities(
          currentToken,
          controller.signal,
        )

        setCapabilities(response)
        setCapabilitiesError(null)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setCapabilities(null)
        setCapabilitiesError(
          requestError instanceof ApiError
            ? requestError.message
            : 'Não foi possível verificar a disponibilidade do Pix.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingCapabilities(false)
        }
      }
    }

    void loadCapabilities()

    return () => {
      controller.abort()
    }
  }, [auth.token])

  const pixPayment = useMemo(() => {
    if (!order) {
      return undefined
    }

    return [...order.payments]
      .reverse()
      .find((payment) => payment.method === 'pix')
  }, [order])

  const pixCode = getStringProviderData(
    pixPayment,
    'qr_code',
  )

  const pixQrCodeBase64 = getStringProviderData(
    pixPayment,
    'qr_code_base64',
  )

  const pixTicketUrl = getStringProviderData(
    pixPayment,
    'ticket_url',
  )

  const pixImageSource = pixQrCodeBase64
    ? (
      pixQrCodeBase64.startsWith('data:image')
        ? pixQrCodeBase64
        : `data:image/png;base64,${pixQrCodeBase64}`
    )
    : ''

  async function handleCreatePix() {
    if (
      !auth.token
      || !publicId
      || !capabilities?.pix.available
    ) {
      return
    }

    try {
      setIsCreatingPix(true)
      setPaymentError(null)
      setPixCopied(false)

      const payment = await createPixPayment(
        auth.token,
        publicId,
      )

      setOrder((currentOrder) => {
        if (!currentOrder) {
          return currentOrder
        }

        const existingPaymentIndex =
          currentOrder.payments.findIndex(
            (currentPayment) => (
              currentPayment.id === payment.id
            ),
          )

        const nextPayments = [...currentOrder.payments]

        if (existingPaymentIndex >= 0) {
          nextPayments[existingPaymentIndex] = payment
        } else {
          nextPayments.push(payment)
        }

        return {
          ...currentOrder,
          payments: nextPayments,
          payment_status: payment.status,
        }
      })
    } catch (requestError) {
      setPaymentError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível gerar o pagamento Pix.',
      )
    } finally {
      setIsCreatingPix(false)
    }
  }

  async function handleCopyPix() {
    if (!pixCode) {
      return
    }

    try {
      await navigator.clipboard.writeText(pixCode)
      setPixCopied(true)
      setPaymentError(null)
    } catch {
      setPaymentError(
        'Não foi possível copiar o código Pix automaticamente.',
      )
    }
  }

  async function handleCancelOrder() {
    if (
      !auth.token
      || !publicId
      || !canCancelOrder
    ) {
      return
    }

    const confirmed = window.confirm(
      'Tem certeza que deseja cancelar este pedido? '
      + 'O estoque reservado será devolvido.',
    )

    if (!confirmed) {
      return
    }

    try {
      setIsCancellingOrder(true)
      setCancelError(null)

      const cancelledOrder = await cancelOrder(
        auth.token,
        publicId,
      )

      setOrder(cancelledOrder)
      setPaymentError(null)
      setPixCopied(false)
    } catch (requestError) {
      setCancelError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível cancelar o pedido.',
      )
    } finally {
      setIsCancellingOrder(false)
    }
  }

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

  const paymentIsFinal =
    order.payment_status === 'paid'
    || order.payment_status === 'refunded'

  const orderIsCancelled =
    order.status === 'cancelled'

  const pixAvailable =
    capabilities?.pix.available === true

  const canGeneratePix =
    pixAvailable
    && !paymentIsFinal
    && !orderIsCancelled

  const hasExternalPayment = order.payments.some(
    (payment) => (
      Boolean(payment.provider_order_id)
      || Boolean(payment.external_id)
    ),
  )

  const canCancelOrder =
    order.status === 'pending'
    && !paymentIsFinal
    && !hasExternalPayment

  return (
    <section className="page-section">
      <div className="container checkout-success">
        <p className="eyebrow">Pedido</p>

        <h1>Pedido recebido</h1>

        <p className="page-intro">
          Seu pedido está registrado no sistema. Você pode acompanhar
          o status e, quando disponível, iniciar o pagamento por Pix.
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

        <section
          className="pix-payment"
          aria-labelledby="pix-payment-title"
        >
          <div className="pix-payment__heading">
            <div>
              <p className="eyebrow">Pagamento</p>
              <h2 id="pix-payment-title">Pix</h2>
            </div>

            <span className="pix-payment__status">
              {getStatusLabel(
                paymentStatusLabels,
                order.payment_status,
              )}
            </span>
          </div>

          {paymentIsFinal ? (
            <p className="pix-payment__message">
              Este pedido não possui pagamento Pix pendente.
            </p>
          ) : orderIsCancelled ? (
            <p className="pix-payment__message">
              Pedidos cancelados não podem receber novos pagamentos.
            </p>
          ) : pixCode ? (
            <div className="pix-payment__content">
              {pixImageSource && (
                <img
                  className="pix-payment__qr"
                  src={pixImageSource}
                  alt="QR Code do pagamento Pix"
                />
              )}

              <div className="pix-payment__details">
                <strong>Pix gerado</strong>

                <p>
                  Use o QR Code ou copie o código Pix abaixo.
                </p>

                <code className="pix-payment__code">
                  {pixCode}
                </code>

                <div className="pix-payment__actions">
                  <button
                    className="button-primary"
                    type="button"
                    onClick={() => {
                      void handleCopyPix()
                    }}
                  >
                    {pixCopied
                      ? 'Código copiado'
                      : 'Copiar código Pix'}
                  </button>

                  {pixTicketUrl && (
                    <a
                      className="button-secondary"
                      href={pixTicketUrl}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Abrir pagamento
                    </a>
                  )}
                </div>
              </div>
            </div>
          ) : isLoadingCapabilities ? (
            <p className="pix-payment__message">
              Verificando disponibilidade do Pix...
            </p>
          ) : capabilitiesError ? (
            <p
              className="pix-payment__message"
              role="alert"
            >
              {capabilitiesError}
            </p>
          ) : canGeneratePix ? (
            <div className="pix-payment__ready">
              <p>
                Gere um Pix para este pedido. O valor será definido
                pelo backend com base no total registrado.
              </p>

              <button
                className="button-primary"
                disabled={isCreatingPix}
                type="button"
                onClick={() => {
                  void handleCreatePix()
                }}
              >
                {isCreatingPix
                  ? 'Gerando Pix...'
                  : 'Gerar pagamento Pix'}
              </button>
            </div>
          ) : (
            <div className="pix-payment__unavailable">
              <strong>Pix indisponível neste ambiente</strong>

              <p>
                A integração está preparada, mas as credenciais do
                provedor de pagamento não estão configuradas neste
                ambiente de desenvolvimento.
              </p>
            </div>
          )}

          {paymentError && (
            <p
              className="pix-payment__error"
              role="alert"
            >
              {paymentError}
            </p>
          )}
        </section>

        {(orderIsCancelled || order.status === 'pending') && (
          <section
            className="order-cancellation"
            aria-labelledby="order-cancellation-title"
          >
            <div>
              <p className="eyebrow">Pedido</p>

              <h2 id="order-cancellation-title">
                {orderIsCancelled
                  ? 'Pedido cancelado'
                  : 'Cancelar pedido'}
              </h2>
            </div>

            {orderIsCancelled ? (
              <p className="order-cancellation__message">
                Este pedido foi cancelado e não pode receber
                novos pagamentos.
              </p>
            ) : canCancelOrder ? (
              <>
                <p className="order-cancellation__message">
                  Você pode cancelar este pedido enquanto ele
                  ainda estiver pendente. Os itens reservados
                  voltarão ao estoque.
                </p>

                <div className="order-cancellation__actions">
                  <button
                    className="button-danger"
                    disabled={isCancellingOrder}
                    type="button"
                    onClick={() => {
                      void handleCancelOrder()
                    }}
                  >
                    {isCancellingOrder
                      ? 'Cancelando pedido...'
                      : 'Cancelar pedido'}
                  </button>
                </div>
              </>
            ) : hasExternalPayment ? (
              <p className="order-cancellation__message">
                O pagamento deste pedido já foi iniciado.
                O cancelamento automático não está disponível
                neste momento.
              </p>
            ) : (
              <p className="order-cancellation__message">
                Este pedido não pode mais ser cancelado
                automaticamente.
              </p>
            )}

            {cancelError && (
              <p
                className="order-cancellation__error"
                role="alert"
              >
                {cancelError}
              </p>
            )}
          </section>
        )}
        <div className="checkout-success__actions">
          <Link
            className="button-primary"
            to="/catalogo"
          >
            Continuar comprando
          </Link>

          <Link
            className="button-secondary"
            to="/pedidos"
          >
            Meus pedidos
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
