import type {
  Category,
  PaginatedProducts,
  Product,
} from '../types/catalog'

import { apiGet } from './api'

export function getCategories(
  signal?: AbortSignal,
) {
  return apiGet<Category[]>(
    '/catalog/categories/',
    signal,
  )
}

export function getProducts(
  signal?: AbortSignal,
) {
  return apiGet<PaginatedProducts>(
    '/catalog/products/',
    signal,
  )
}

export function getProduct(
  slug: string,
  signal?: AbortSignal,
) {
  return apiGet<Product>(
    `/catalog/products/${encodeURIComponent(slug)}/`,
    signal,
  )
}
