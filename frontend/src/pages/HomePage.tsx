import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { getCategories } from '../services/catalog'
import type { Category } from '../types/catalog'

export function HomePage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoadingCategories, setIsLoadingCategories] =
    useState(true)
  const [categoryError, setCategoryError] =
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
    </>
  )
}
