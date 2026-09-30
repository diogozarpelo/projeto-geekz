import { apiRequest } from './api'
import type {
  CheckoutPayload,
  Order,
  PaginatedOrders,
  Payment,
  PaymentCapabilities,
} from '../types/orders'

export function createOrderFromCart(
  token: string,
  payload: CheckoutPayload,
  signal?: AbortSignal,
) {
  return apiRequest<Order>(
    '/orders/checkout/',
    {
      method: 'POST',
      token,
      body: payload,
      signal,
    },
  )
}

export function getOrder(
  token: string,
  publicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<Order>(
    `/orders/${publicId}/`,
    {
      token,
      signal,
    },
  )
}

export function getOrders(
  token: string,
  page: number,
  signal?: AbortSignal,
) {
  return apiRequest<PaginatedOrders>(
    `/orders/?page=${page}`,
    {
      token,
      signal,
    },
  )
}

export function getPaymentCapabilities(
  token: string,
  signal?: AbortSignal,
) {
  return apiRequest<PaymentCapabilities>(
    '/orders/payment-capabilities/',
    {
      token,
      signal,
    },
  )
}

export function createPixPayment(
  token: string,
  publicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<Payment>(
    `/orders/${publicId}/payments/`,
    {
      method: 'POST',
      token,
      body: {
        method: 'pix',
      },
      signal,
    },
  )
}
