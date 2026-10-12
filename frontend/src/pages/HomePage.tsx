import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ProductCard } from '../components/ui/ProductCard'
import {
  getCategories,
  getProducts,
} from '../services/catalog'
import type {
  Category,
  Product,
} from '../types/catalog'

export function HomePage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoadingCategories, setIsLoadingCategories] =
    useState(true)
  const [categoryError, setCategoryError] =
    useState<string | null>(null)

  const [featuredProducts, setFeaturedProducts] =
    useState<Product[]>([])
  const [isLoadingFeatured, setIsLoadingFeatured] =
    useState(true)
  const [featuredError, setFeaturedError] =
    useState<string | null>(null)

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
          'Não foi possível carregar as categorias agora.',
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

    async function loadFeaturedProducts() {
      try {
        setIsLoadingFeatured(true)
        setFeaturedError(null)

        const response = await getProducts(
          {
            featured: true,
            pageSize: 3,
          },
          controller.signal,
        )

        setFeaturedProducts(response.results)
      } catch (requestError) {
        if (
          requestError instanceof DOMException
          && requestError.name === 'AbortError'
        ) {
          return
        }

        setFeaturedError(
          'Não foi possível carregar os destaques agora.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingFeatured(false)
        }
      }
    }

    void loadFeaturedProducts()

    return () => {
      controller.abort()
    }
  }, [])

  return (
    <>
      <section className="home-hero">
        <div className="container home-hero__content">
          <p className="eyebrow">Geekz</p>

          <h1>Vista o universo que você curte.</h1>

          <p className="page-intro">
            Camisas inspiradas em games, animes, filmes e séries
            para levar suas paixões para o dia a dia.
          </p>

          <Link
            className="button-primary"
            to="/catalogo"
          >
            Explorar catálogo
          </Link>
        </div>
      </section>

      <section
        className="home-categories"
        aria-labelledby="home-categories-title"
      >
        <div className="container">
          <div className="home-section__header">
            <div>
              <p className="eyebrow">
                Escolha seu universo
              </p>

              <h2 id="home-categories-title">
                Explore por categoria
              </h2>

              <p className="home-section__intro">
                Entre direto no estilo que combina com você.
              </p>
            </div>

            <Link
              className="home-section__link"
              to="/catalogo"
            >
              Ver catálogo completo
            </Link>
          </div>

          {isLoadingCategories && (
            <p
              className="home-status"
              role="status"
            >
              Carregando categorias...
            </p>
          )}

          {categoryError && (
            <p
              className="home-status home-status--error"
              role="alert"
            >
              {categoryError}
            </p>
          )}

          {!isLoadingCategories
            && !categoryError
            && categories.length > 0 && (
              <div className="home-category-grid">
                {categories.map((category) => (
                  <Link
                    className="home-category-card"
                    key={category.slug}
                    to={
                      `/catalogo?category=${
                        encodeURIComponent(category.slug)
                      }`
                    }
                  >
                    <span className="home-category-card__eyebrow">
                      Categoria
                    </span>

                    <strong>{category.name}</strong>

                    <p>
                      {category.description
                        || `Explore produtos de ${category.name}.`}
                    </p>

                    <span className="home-category-card__action">
                      Ver produtos →
                    </span>
                  </Link>
                ))}
              </div>
          )}

          {!isLoadingCategories
            && !categoryError
            && categories.length === 0 && (
              <p className="home-status">
                As categorias da loja aparecerão aqui
                quando estiverem disponíveis.
              </p>
          )}
        </div>
      </section>

      <section
        className="home-featured"
        aria-labelledby="home-featured-title"
      >
        <div className="container">
          <div className="home-section__header">
            <div>
              <p className="eyebrow">
                Seleção Geekz
              </p>

              <h2 id="home-featured-title">
                Produtos em destaque
              </h2>

              <p className="home-section__intro">
                Uma seleção especial de produtos para começar
                a explorar o universo Geekz.
              </p>
            </div>

            <Link
              className="home-section__link"
              to="/catalogo"
            >
              Ver todos os produtos
            </Link>
          </div>

          {isLoadingFeatured && (
            <p
              className="home-status"
              role="status"
            >
              Carregando destaques...
            </p>
          )}

          {featuredError && (
            <p
              className="home-status home-status--error"
              role="alert"
            >
              {featuredError}
            </p>
          )}

          {!isLoadingFeatured
            && !featuredError
            && featuredProducts.length > 0 && (
              <div className="product-grid">
                {featuredProducts.map((product) => (
                  <ProductCard
                    key={product.slug}
                    product={product}
                  />
                ))}
              </div>
          )}

          {!isLoadingFeatured
            && !featuredError
            && featuredProducts.length === 0 && (
              <p className="home-status">
                Os produtos em destaque aparecerão aqui
                quando forem selecionados no catálogo.
              </p>
          )}
        </div>
      </section>
    </>
  )
}
