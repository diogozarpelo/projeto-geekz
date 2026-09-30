import { apiRequest } from './api'
import type {
  CheckoutPayload,
  Order,
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
