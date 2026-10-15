import { apiRequest } from './api'
import {
  getStoredCartPublicId,
  storeCartPublicId,
} from './cartStorage'
import type {
  AddCartItemPayload,
  Cart,
  UpdateCartItemPayload,
} from '../types/cart'

function rememberCart(cart: Cart) {
  storeCartPublicId(cart.public_id)
  return cart
}

export async function getActiveCart(
  token?: string | null,
  signal?: AbortSignal,
) {
  const cart = await apiRequest<Cart>(
    '/cart/',
    {
      token,
      cartPublicId: getStoredCartPublicId(),
      signal,
    },
  )

  return rememberCart(cart)
}

export async function addCartItem(
  token: string | null | undefined,
  payload: AddCartItemPayload,
  signal?: AbortSignal,
) {
  const cart = await apiRequest<Cart>(
    '/cart/items/',
    {
      method: 'POST',
      token,
      cartPublicId: getStoredCartPublicId(),
      body: payload,
      signal,
    },
  )

  return rememberCart(cart)
}

export async function updateCartItem(
  token: string | null | undefined,
  itemId: number,
  payload: UpdateCartItemPayload,
  signal?: AbortSignal,
) {
  const cart = await apiRequest<Cart>(
    `/cart/items/${itemId}/`,
    {
      method: 'PATCH',
      token,
      cartPublicId: getStoredCartPublicId(),
      body: payload,
      signal,
    },
  )

  return rememberCart(cart)
}

export async function removeCartItem(
  token: string | null | undefined,
  itemId: number,
  signal?: AbortSignal,
) {
  const cart = await apiRequest<Cart>(
    `/cart/items/${itemId}/`,
    {
      method: 'DELETE',
      token,
      cartPublicId: getStoredCartPublicId(),
      signal,
    },
  )

  return rememberCart(cart)
}
