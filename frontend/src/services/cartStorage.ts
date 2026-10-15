const CART_PUBLIC_ID_KEY = 'geekz.cart.publicId'

export function getStoredCartPublicId() {
  const value = window.localStorage.getItem(
    CART_PUBLIC_ID_KEY,
  )

  return value?.trim() || null
}

export function storeCartPublicId(
  publicId: string,
) {
  window.localStorage.setItem(
    CART_PUBLIC_ID_KEY,
    publicId,
  )
}

export function clearStoredCartPublicId() {
  window.localStorage.removeItem(
    CART_PUBLIC_ID_KEY,
  )
}
