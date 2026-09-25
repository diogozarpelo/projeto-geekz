export interface Category {
  name: string
  slug: string
  description: string
}

export interface ProductColor {
  name: string
  slug: string
  hex_code: string
}

export interface ProductSize {
  name: string
  slug: string
}

export interface ProductVariant {
  id: number
  sku: string
  color: ProductColor
  size: ProductSize
  effective_price: string
  stock_quantity: number
  is_in_stock: boolean
}

export interface ProductImage {
  id: number
  image: string
  color: ProductColor | null
  alt_text: string
  sort_order: number
  is_primary: boolean
}

export interface Product {
  name: string
  slug: string
  short_description: string
  description: string
  base_price: string
  compare_at_price: string | null
  is_featured: boolean
  is_in_stock: boolean
  categories: Category[]
  variants: ProductVariant[]
  images: ProductImage[]
  created_at: string
  updated_at: string
}

export interface PaginatedProducts {
  count: number
  next: string | null
  previous: string | null
  results: Product[]
}
