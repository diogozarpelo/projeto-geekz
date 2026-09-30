import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ProductPurchaseActions } from '../components/ui/ProductPurchaseActions'
import { ApiError } from '../services/api'
import { getProduct } from '../services/catalog'
import type {
  Product,
  ProductColor,
  ProductSize,
} from '../types/catalog'
import { formatCurrencyBRL } from '../utils/currency'

export function ProductPage() {
  const { slug } = useParams()

  const [product, setProduct] = useState<Product | null>(null)
  const [selectedColorSlug, setSelectedColorSlug] = useState('')
  const [selectedSizeSlug, setSelectedSizeSlug] = useState('')
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null)

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

        const preferredVariant = (
          response.variants.find(
            (variant) => variant.is_in_stock,
          )
          ?? response.variants[0]
        )

        const preferredImage = (
          response.images.find(
            (image) => image.is_primary,
          )
          ?? response.images[0]
        )

        setProduct(response)
        setSelectedColorSlug(
          preferredVariant?.color.slug ?? '',
        )
        setSelectedSizeSlug(
          preferredVariant?.size.slug ?? '',
        )
        setSelectedImageId(
          preferredImage?.id ?? null,
        )
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

        setProduct(null)
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

  const colors = product.variants.reduce<ProductColor[]>(
    (items, variant) => {
      if (
        !items.some(
          (color) => color.slug === variant.color.slug,
        )
      ) {
        items.push(variant.color)
      }

      return items
    },
    [],
  )

  const sizes = product.variants.reduce<ProductSize[]>(
    (items, variant) => {
      if (
        !items.some(
          (size) => size.slug === variant.size.slug,
        )
      ) {
        items.push(variant.size)
      }

      return items
    },
    [],
  )

  const selectedVariant = product.variants.find(
    (variant) => (
      variant.color.slug === selectedColorSlug
      && variant.size.slug === selectedSizeSlug
    ),
  )

  const filteredImages = selectedColorSlug
    ? product.images.filter(
        (image) => (
          image.color === null
          || image.color.slug === selectedColorSlug
        ),
      )
    : product.images

  const galleryImages = (
    filteredImages.length > 0
      ? filteredImages
      : product.images
  )

  const selectedImage = (
    galleryImages.find(
      (image) => image.id === selectedImageId,
    )
    ?? galleryImages.find(
      (image) => image.is_primary,
    )
    ?? galleryImages[0]
  )

  const currentPrice = (
    selectedVariant?.effective_price
    ?? product.base_price
  )

  const showComparePrice = (
    product.compare_at_price !== null
    && Number(product.compare_at_price) > Number(currentPrice)
  )

  function selectColor(colorSlug: string) {
    const currentProduct = product

    if (!currentProduct) {
      return
    }

    const variantsForColor = currentProduct.variants.filter(
      (variant) => variant.color.slug === colorSlug,
    )

    const nextVariant = (
      variantsForColor.find(
        (variant) => (
          variant.size.slug === selectedSizeSlug
          && variant.is_in_stock
        ),
      )
      ?? variantsForColor.find(
        (variant) => variant.is_in_stock,
      )
      ?? variantsForColor[0]
    )

    const colorImages = currentProduct.images.filter(
      (image) => image.color?.slug === colorSlug,
    )

    const genericImages = currentProduct.images.filter(
      (image) => image.color === null,
    )

    const nextImage = (
      colorImages.find(
        (image) => image.is_primary,
      )
      ?? colorImages[0]
      ?? genericImages.find(
        (image) => image.is_primary,
      )
      ?? genericImages[0]
      ?? currentProduct.images[0]
    )

    setSelectedColorSlug(colorSlug)
    setSelectedSizeSlug(
      nextVariant?.size.slug ?? '',
    )
    setSelectedImageId(
      nextImage?.id ?? null,
    )
  }

  function selectSize(sizeSlug: string) {
    const currentProduct = product

    if (!currentProduct) {
      return
    }

    const variant = currentProduct.variants.find(
      (item) => (
        item.color.slug === selectedColorSlug
        && item.size.slug === sizeSlug
      ),
    )

    if (!variant || !variant.is_in_stock) {
      return
    }

    setSelectedSizeSlug(sizeSlug)
  }

  return (
    <section className="page-section">
      <div className="container">
        <Link
          className="product-detail__back"
          to="/catalogo"
        >
          ← Voltar ao catálogo
        </Link>

        <div className="product-detail">
          <div className="product-gallery">
            <div className="product-gallery__main">
              {selectedImage ? (
                <img
                  src={selectedImage.image}
                  alt={
                    selectedImage.alt_text
                    || product.name
                  }
                />
              ) : (
                <div className="product-gallery__placeholder">
                  Geekz
                </div>
              )}
            </div>

            {galleryImages.length > 1 && (
              <div
                className="product-gallery__thumbnails"
                aria-label="Imagens do produto"
              >
                {galleryImages.map((image) => (
                  <button
                    className={
                      selectedImage?.id === image.id
                        ? (
                          'product-gallery__thumbnail '
                          + 'product-gallery__thumbnail--active'
                        )
                        : 'product-gallery__thumbnail'
                    }
                    type="button"
                    key={image.id}
                    aria-pressed={
                      selectedImage?.id === image.id
                    }
                    onClick={() => {
                      setSelectedImageId(image.id)
                    }}
                  >
                    <img
                      src={image.image}
                      alt={
                        image.alt_text
                        || product.name
                      }
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="product-detail__content">
            {product.categories.length > 0 && (
              <p className="eyebrow">
                {product.categories
                  .map((category) => category.name)
                  .join(' • ')}
              </p>
            )}

            <h1>{product.name}</h1>

            {product.short_description && (
              <p className="product-detail__intro">
                {product.short_description}
              </p>
            )}

            <div className="product-detail__pricing">
              <strong>
                {formatCurrencyBRL(currentPrice)}
              </strong>

              {showComparePrice && (
                <span>
                  {formatCurrencyBRL(
                    product.compare_at_price ?? currentPrice,
                  )}
                </span>
              )}
            </div>

            <p
              className={
                selectedVariant?.is_in_stock
                  ? 'product-detail__stock'
                  : (
                    'product-detail__stock '
                    + 'product-detail__stock--out'
                  )
              }
            >
              {selectedVariant
                ? (
                    selectedVariant.is_in_stock
                      ? (
                        `${selectedVariant.stock_quantity} `
                        + 'unidade(s) em estoque'
                      )
                      : 'Variação indisponível'
                  )
                : (
                    product.is_in_stock
                      ? 'Produto em estoque'
                      : 'Produto indisponível'
                  )}
            </p>

            {colors.length > 0 && (
              <fieldset className="product-options">
                <legend>Cor</legend>

                <div className="product-options__list">
                  {colors.map((color) => (
                    <button
                      className={
                        selectedColorSlug === color.slug
                          ? (
                            'product-option '
                            + 'product-option--active'
                          )
                          : 'product-option'
                      }
                      type="button"
                      key={color.slug}
                      aria-pressed={
                        selectedColorSlug === color.slug
                      }
                      onClick={() => {
                        selectColor(color.slug)
                      }}
                    >
                      {color.hex_code && (
                        <span
                          className="product-option__color"
                          style={{
                            backgroundColor: color.hex_code,
                          }}
                          aria-hidden="true"
                        />
                      )}

                      {color.name}
                    </button>
                  ))}
                </div>
              </fieldset>
            )}

            {sizes.length > 0 && (
              <fieldset className="product-options">
                <legend>Tamanho</legend>

                <div className="product-options__list">
                  {sizes.map((size) => {
                    const variant = product.variants.find(
                      (item) => (
                        item.color.slug === selectedColorSlug
                        && item.size.slug === size.slug
                      ),
                    )

                    const isAvailable = Boolean(
                      variant?.is_in_stock,
                    )

                    return (
                      <button
                        className={
                          selectedSizeSlug === size.slug
                            ? (
                              'product-option '
                              + 'product-option--active'
                            )
                            : 'product-option'
                        }
                        type="button"
                        key={size.slug}
                        disabled={!isAvailable}
                        aria-pressed={
                          selectedSizeSlug === size.slug
                        }
                        onClick={() => {
                          selectSize(size.slug)
                        }}
                      >
                        {size.name}
                      </button>
                    )
                  })}
                </div>
              </fieldset>
            )}

            <ProductPurchaseActions
              variant={selectedVariant}
            />
            {selectedVariant && (
              <div className="product-detail__meta">
                <span>
                  SKU: {selectedVariant.sku}
                </span>
              </div>
            )}
          </div>
        </div>

        {product.description && (
          <section
            className="product-description"
            aria-labelledby="product-description-title"
          >
            <h2 id="product-description-title">
              Sobre o produto
            </h2>

            <p>
              {product.description}
            </p>
          </section>
        )}
      </div>
    </section>
  )
}
