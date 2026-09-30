export type CartItem = {
  id: number
  variant_id: number
  product_name: string
  product_slug: string
  sku: string
  color_name: string
  color_slug: string
  color_hex: string
  size_name: string
  size_slug: string
  unit_price: string
  quantity: number
  total_price: string
  available_stock: number
  is_in_stock: boolean
}

export type Cart = {
  public_id: string
  status: string
  total_items: number
  subtotal: string
  items: CartItem[]
  created_at: string
  updated_at: string
}

export type AddCartItemPayload = {
  variant_id: number
  quantity?: number
}

export type UpdateCartItemPayload = {
  quantity: number
}
