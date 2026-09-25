import type {
  Category,
  PaginatedProducts,
  Product,
} from '../types/catalog'

import { apiGet } from './api'

export interface ProductListParams {
  category?: string
  search?: string
  page?: number
  pageSize?: number
}

export function getCategories(
  signal?: AbortSignal,
) {
  return apiGet<Category[]>(
    '/catalog/categories/',
    signal,
  )
}

export function getProducts(
  params: ProductListParams = {},
  signal?: AbortSignal,
) {
  const searchParams = new URLSearchParams()

  if (params.category) {
    searchParams.set(
      'category',
      params.category,
    )
  }

  if (params.search) {
    searchParams.set(
      'search',
      params.search,
    )
  }

  if (params.page) {
    searchParams.set(
      'page',
      String(params.page),
    )
  }

  if (params.pageSize) {
    searchParams.set(
      'page_size',
      String(params.pageSize),
    )
  }

  const query = searchParams.toString()

  return apiGet<PaginatedProducts>(
    `/catalog/products/${query ? `?${query}` : ''}`,
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
