import { useEffect, useState } from 'react'

import {
  getCategories,
  getProducts,
} from '../services/catalog'
import type {
  Category,
  Product,
} from '../types/catalog'

export function CatalogPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [productCount, setProductCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadCatalog() {
      try {
        setIsLoading(true)
        setError(null)

        const [
          categoriesResponse,
          productsResponse,
        ] = await Promise.all([
          getCategories(controller.signal),
          getProducts(controller.signal),
        ])

        setCategories(categoriesResponse)
        setProducts(productsResponse.results)
        setProductCount(productsResponse.count)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setError(
          'Não foi possível carregar o catálogo agora.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadCatalog()

    return () => {
      controller.abort()
    }
  }, [])

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Catálogo</p>
        <h1>Produtos Geekz</h1>

        <p className="page-intro">
          Explore nossas categorias e encontre sua próxima camiseta.
        </p>

        {isLoading && (
          <p className="catalog-status">
            Carregando catálogo...
          </p>
        )}

        {error && (
          <p
            className="catalog-status catalog-status--error"
            role="alert"
          >
            {error}
          </p>
        )}

        {!isLoading && !error && (
          <>
            <section
              className="catalog-section"
              aria-labelledby="catalog-categories-title"
            >
              <h2 id="catalog-categories-title">
                Categorias
              </h2>

              <div className="category-list">
                {categories.map((category) => (
                  <span
                    className="category-chip"
                    key={category.slug}
                  >
                    {category.name}
                  </span>
                ))}
              </div>
            </section>

            <section
              className="catalog-section"
              aria-labelledby="catalog-products-title"
            >
              <div className="catalog-section__header">
                <h2 id="catalog-products-title">
                  Produtos
                </h2>

                <span className="catalog-count">
                  {productCount} produto(s)
                </span>
              </div>

              {products.length === 0 ? (
                <div className="empty-state">
                  <h3>
                    Nenhum produto disponível ainda.
                  </h3>

                  <p>
                    O catálogo já está conectado ao backend.
                    Assim que produtos ativos forem cadastrados,
                    eles aparecerão aqui automaticamente.
                  </p>
                </div>
              ) : (
                <div className="product-grid">
                  {products.map((product) => (
                    <article
                      className="product-card"
                      key={product.slug}
                    >
                      <p className="product-card__category">
                        {product.categories
                          .map((category) => category.name)
                          .join(' • ')}
                      </p>

                      <h3>{product.name}</h3>

                      <p>
                        {product.short_description}
                      </p>

                      <strong>
                        R$ {product.base_price}
                      </strong>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </section>
  )
}
