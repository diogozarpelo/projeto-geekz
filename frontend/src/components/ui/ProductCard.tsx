import { Link } from 'react-router-dom'

import type { Product } from '../../types/catalog'
import { formatCurrencyBRL } from '../../utils/currency'

interface ProductCardProps {
  product: Product
}

export function ProductCard({
  product,
}: ProductCardProps) {
  const primaryImage = (
    product.images.find((image) => image.is_primary)
    ?? product.images[0]
  )

  return (
    <article className="product-card">
      <Link
        className="product-card__media"
        to={`/produto/${product.slug}`}
        aria-label={`Ver ${product.name}`}
      >
        {primaryImage ? (
          <img
            src={primaryImage.image}
            alt={primaryImage.alt_text || product.name}
            loading="lazy"
          />
        ) : (
          <span className="product-card__placeholder">
            Geekz
          </span>
        )}
      </Link>

      <div className="product-card__body">
        {product.categories.length > 0 && (
          <p className="product-card__category">
            {product.categories
              .map((category) => category.name)
              .join(' • ')}
          </p>
        )}

        <h3>
          <Link to={`/produto/${product.slug}`}>
            {product.name}
          </Link>
        </h3>

        {product.short_description && (
          <p className="product-card__description">
            {product.short_description}
          </p>
        )}

        <div className="product-card__pricing">
          <strong>
            {formatCurrencyBRL(product.base_price)}
          </strong>

          {product.compare_at_price && (
            <span className="product-card__compare-price">
              {formatCurrencyBRL(product.compare_at_price)}
            </span>
          )}
        </div>

        <p
          className={
            product.is_in_stock
              ? 'product-card__stock'
              : 'product-card__stock product-card__stock--out'
          }
        >
          {product.is_in_stock
            ? 'Em estoque'
            : 'Indisponível'}
        </p>
      </div>
    </article>
  )
}
