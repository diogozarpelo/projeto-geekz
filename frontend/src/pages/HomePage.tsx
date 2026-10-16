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
        <div className="container home-hero__layout">
          <div className="home-hero__content">
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

          <div
            className="home-hero__visual"
            aria-hidden="true"
          >
            <div className="home-hero__visual-grid">
              <span className="home-hero__visual-card">
                Games
              </span>

              <span className="home-hero__visual-card">
                Animes
              </span>

              <span className="home-hero__visual-card">
                Filmes &amp; séries
              </span>
            </div>

            <span className="home-hero__visual-mark">
              geek<span>Z</span>
            </span>
          </div>
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
                    <span
                      className="home-category-card__visual"
                      data-category={category.slug}
                      aria-hidden="true"
                    >
                      <span>
                        {category.name.charAt(0).toUpperCase()}
                      </span>
                    </span>

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

      <section
        className="home-benefits"
        aria-labelledby="home-benefits-title"
      >
        <div className="container">
          <div className="home-section__header">
            <div>
              <p className="eyebrow">
                Experiência Geekz
              </p>

              <h2 id="home-benefits-title">
                Feito para comprar sem complicação
              </h2>

              <p className="home-section__intro">
                Do catálogo ao acompanhamento do pedido,
                cada etapa foi pensada para ser simples
                e direta.
              </p>
            </div>
          </div>

          <div className="home-benefit-grid">
            <article className="home-benefit-card">
              <span className="home-benefit-card__number">
                01
              </span>

              <h3>Catálogo organizado</h3>

              <p>
                Explore produtos por categoria, pesquise
                pelo que procura e confira disponibilidade
                antes de comprar.
              </p>
            </article>

            <article className="home-benefit-card">
              <span className="home-benefit-card__number">
                02
              </span>

              <h3>Checkout direto</h3>

              <p>
                Revise o carrinho, informe o endereço
                de entrega e conclua o pedido em um fluxo
                único.
              </p>
            </article>

            <article className="home-benefit-card">
              <span className="home-benefit-card__number">
                03
              </span>

              <h3>Pedidos na sua conta</h3>

              <p>
                Acesse seu histórico, consulte os detalhes
                de cada pedido e mantenha seus dados
                organizados em um só lugar.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section
        className="home-faq"
        aria-labelledby="home-faq-title"
      >
        <div className="container">
          <div className="home-section__header">
            <div>
              <p className="eyebrow">
                Dúvidas frequentes
              </p>

              <h2 id="home-faq-title">
                Antes de escolher sua próxima camiseta
              </h2>

              <p className="home-section__intro">
                Algumas respostas rápidas sobre como
                navegar e comprar na Geekz.
              </p>
            </div>
          </div>

          <div className="home-faq__list">
            <details className="home-faq__item">
              <summary>
                Como encontro produtos de uma categoria?
              </summary>

              <p>
                Você pode escolher uma categoria diretamente
                na Home ou usar os filtros disponíveis
                no catálogo.
              </p>
            </details>

            <details className="home-faq__item">
              <summary>
                Como sei se um produto está disponível?
              </summary>

              <p>
                Os produtos exibem a disponibilidade atual,
                e a página de detalhes permite conferir
                as variações disponíveis antes da compra.
              </p>
            </details>

            <details className="home-faq__item">
              <summary>
                Posso acompanhar meus pedidos?
              </summary>

              <p>
                Sim. Depois de entrar na sua conta,
                a área Meus pedidos reúne o histórico
                e os detalhes das compras realizadas.
              </p>
            </details>

            <details className="home-faq__item">
              <summary>
                Posso salvar meu endereço para outra compra?
              </summary>

              <p>
                Sim. Você pode manter um endereço padrão
                na sua conta ou optar por salvá-lo durante
                o checkout.
              </p>
            </details>
          </div>
        </div>
      </section>
    </>
  )
}
