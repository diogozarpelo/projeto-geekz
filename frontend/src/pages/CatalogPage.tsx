import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import { ProductCard } from '../components/ui/ProductCard'
import {
  getCategories,
  getProducts,
} from '../services/catalog'
import type {
  Category,
  Product,
} from '../types/catalog'

const PAGE_SIZE = 12

export function CatalogPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [productCount, setProductCount] = useState(0)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [page, setPage] = useState(1)

  const [isLoadingCategories, setIsLoadingCategories] = useState(true)
  const [isLoadingProducts, setIsLoadingProducts] = useState(true)

  const [categoryError, setCategoryError] = useState<string | null>(null)
  const [productError, setProductError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadCategories() {
      try {
        setIsLoadingCategories(true)
        setCategoryError(null)

        const response = await getCategories(
          controller.signal,
        )

        setCategories(response)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setCategoryError(
          'Não foi possível carregar as categorias.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingCategories(false)
        }
      }
    }

    void loadCategories()

    return () => {
      controller.abort()
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    async function loadProducts() {
      try {
        setIsLoadingProducts(true)
        setProductError(null)

        const response = await getProducts(
          {
            category: category || undefined,
            search: search || undefined,
            page,
            pageSize: PAGE_SIZE,
          },
          controller.signal,
        )

        setProducts(response.results)
        setProductCount(response.count)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setProductError(
          'Não foi possível carregar os produtos agora.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingProducts(false)
        }
      }
    }

    void loadProducts()

    return () => {
      controller.abort()
    }
  }, [
    category,
    page,
    search,
  ])

  const totalPages = Math.max(
    1,
    Math.ceil(productCount / PAGE_SIZE),
  )

  function handleSearchSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setSearch(searchInput.trim())
    setPage(1)
  }

  function handleCategoryChange(
    categorySlug: string,
  ) {
    setCategory(categorySlug)
    setPage(1)
  }

  function clearFilters() {
    setSearchInput('')
    setSearch('')
    setCategory('')
    setPage(1)
  }

  const hasFilters = Boolean(
    search || category,
  )

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Catálogo</p>
        <h1>Produtos Geekz</h1>

        <p className="page-intro">
          Explore nossas categorias e encontre sua próxima camiseta.
        </p>

        <div className="catalog-toolbar">
          <form
            className="catalog-search"
            onSubmit={handleSearchSubmit}
          >
            <label
              className="catalog-search__label"
              htmlFor="catalog-search"
            >
              Buscar produtos
            </label>

            <div className="catalog-search__controls">
              <input
                id="catalog-search"
                type="search"
                value={searchInput}
                onChange={(event) => {
                  setSearchInput(event.target.value)
                }}
                placeholder="Nome, descrição ou SKU"
              />

              <button
                className="button-primary catalog-search__button"
                type="submit"
              >
                Buscar
              </button>
            </div>
          </form>

          {hasFilters && (
            <button
              className="button-secondary"
              type="button"
              onClick={clearFilters}
            >
              Limpar filtros
            </button>
          )}
        </div>

        <section
          className="catalog-section"
          aria-labelledby="catalog-categories-title"
        >
          <h2 id="catalog-categories-title">
            Categorias
          </h2>

          {isLoadingCategories && (
            <p className="catalog-status">
              Carregando categorias...
            </p>
          )}

          {categoryError && (
            <p
              className="catalog-status catalog-status--error"
              role="alert"
            >
              {categoryError}
            </p>
          )}

          {!isLoadingCategories && !categoryError && (
            <div
              className="category-list"
              aria-label="Filtrar por categoria"
            >
              <button
                className={
                  category === ''
                    ? 'category-chip category-chip--active'
                    : 'category-chip'
                }
                type="button"
                onClick={() => {
                  handleCategoryChange('')
                }}
              >
                Todas
              </button>

              {categories.map((item) => (
                <button
                  className={
                    category === item.slug
                      ? 'category-chip category-chip--active'
                      : 'category-chip'
                  }
                  type="button"
                  key={item.slug}
                  onClick={() => {
                    handleCategoryChange(item.slug)
                  }}
                >
                  {item.name}
                </button>
              ))}
            </div>
          )}
        </section>

        <section
          className="catalog-section"
          aria-labelledby="catalog-products-title"
        >
          <div className="catalog-section__header">
            <h2 id="catalog-products-title">
              Produtos
            </h2>

            {!isLoadingProducts && !productError && (
              <span className="catalog-count">
                {productCount} produto(s)
              </span>
            )}
          </div>

          {isLoadingProducts && (
            <p className="catalog-status">
              Carregando produtos...
            </p>
          )}

          {productError && (
            <p
              className="catalog-status catalog-status--error"
              role="alert"
            >
              {productError}
            </p>
          )}

          {!isLoadingProducts
            && !productError
            && products.length === 0 && (
              <div className="empty-state">
                <h3>
                  Nenhum produto encontrado.
                </h3>

                <p>
                  {hasFilters
                    ? 'Tente alterar ou limpar os filtros aplicados.'
                    : (
                      'O catálogo já está conectado ao backend. '
                      + 'Assim que produtos ativos forem cadastrados, '
                      + 'eles aparecerão aqui automaticamente.'
                    )}
                </p>
              </div>
            )}

          {!isLoadingProducts
            && !productError
            && products.length > 0 && (
              <>
                <div className="product-grid">
                  {products.map((product) => (
                    <ProductCard
                      key={product.slug}
                      product={product}
                    />
                  ))}
                </div>

                {totalPages > 1 && (
                  <nav
                    className="catalog-pagination"
                    aria-label="Paginação do catálogo"
                  >
                    <button
                      className="button-secondary"
                      type="button"
                      disabled={page <= 1}
                      onClick={() => {
                        setPage((currentPage) => (
                          Math.max(1, currentPage - 1)
                        ))
                      }}
                    >
                      Anterior
                    </button>

                    <span>
                      Página {page} de {totalPages}
                    </span>

                    <button
                      className="button-secondary"
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => {
                        setPage((currentPage) => (
                          Math.min(
                            totalPages,
                            currentPage + 1,
                          )
                        ))
                      }}
                    >
                      Próxima
                    </button>
                  </nav>
                )}
              </>
            )}
        </section>
      </div>
    </section>
  )
}
