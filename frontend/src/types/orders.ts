export type OrderItem = {
  id: number
  product_name: string
  sku: string
  color_name: string
  size_name: string
  unit_price: string
  quantity: number
  total_price: string
}

export type Payment = {
  id: number
  method: string
  provider: string
  status: string
  amount: string
  external_id: string
  provider_order_id: string
  provider_data: Record<string, unknown>
  paid_at: string | null
  refunded_at: string | null
  created_at: string
  updated_at: string
}

export type Order = {
  public_id: string
  customer_name: string
  customer_email: string
  shipping_postal_code: string
  shipping_street: string
  shipping_number: string
  shipping_complement: string
  shipping_neighborhood: string
  shipping_city: string
  shipping_state: string
  shipping_country: string
  status: string
  payment_status: string
  subtotal: string
  shipping_amount: string
  discount_amount: string
  total_amount: string
  notes: string
  items: OrderItem[]
  payments: Payment[]
  created_at: string
  updated_at: string
}

export type CheckoutPayload = {
  cart_public_id: string
  customer_name: string
  customer_email: string
  shipping_postal_code: string
  shipping_street: string
  shipping_number: string
  shipping_complement?: string
  shipping_neighborhood: string
  shipping_city: string
  shipping_state: string
  shipping_country?: string
  notes?: string
}
