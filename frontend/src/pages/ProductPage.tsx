import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ApiError } from '../services/api'
import { getProduct } from '../services/catalog'
import type { Product } from '../types/catalog'

export function ProductPage() {
  const { slug } = useParams()

  const [product, setProduct] = useState<Product | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadProduct() {
      if (!slug) {
        setIsLoading(false)
        setNotFound(true)
        return
      }

      try {
        setIsLoading(true)
        setNotFound(false)
        setError(null)

        const response = await getProduct(
          slug,
          controller.signal,
        )

        setProduct(response)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        if (
          requestError instanceof ApiError
          && requestError.status === 404
        ) {
          setNotFound(true)
          setProduct(null)
          return
        }

        setError(
          'Não foi possível carregar este produto agora.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void loadProduct()

    return () => {
      controller.abort()
    }
  }, [slug])

  if (isLoading) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Produto</p>
          <h1>Carregando produto...</h1>
        </div>
      </section>
    )
  }

  if (notFound) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Produto</p>
          <h1>Produto não encontrado</h1>

          <p className="page-intro">
            O produto solicitado não existe ou não está disponível.
          </p>

          <Link className="button-primary" to="/catalogo">
            Voltar ao catálogo
          </Link>
        </div>
      </section>
    )
  }

  if (error || !product) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Produto</p>
          <h1>Não foi possível carregar o produto</h1>

          <p
            className="page-intro"
            role="alert"
          >
            {error ?? 'Ocorreu um erro inesperado.'}
          </p>

          <Link className="button-primary" to="/catalogo">
            Voltar ao catálogo
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Produto</p>
        <h1>{product.name}</h1>

        <p className="page-intro">
          {product.short_description}
        </p>

        <p>
          {product.description}
        </p>

        <p>
          <strong>
            R$ {product.base_price}
          </strong>
        </p>

        <p>
          {product.is_in_stock
            ? 'Produto em estoque'
            : 'Produto indisponível'}
        </p>

        {product.categories.length > 0 && (
          <div>
            <h2>Categorias</h2>

            <p>
              {product.categories
                .map((category) => category.name)
                .join(' • ')}
            </p>
          </div>
        )}

        {product.variants.length > 0 && (
          <div>
            <h2>Variações</h2>

            <ul>
              {product.variants.map((variant) => (
                <li key={variant.id}>
                  {variant.color.name}
                  {' / '}
                  {variant.size.name}
                  {' - '}
                  R$ {variant.effective_price}
                  {' - '}
                  {variant.is_in_stock
                    ? `${variant.stock_quantity} em estoque`
                    : 'sem estoque'}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}
