import { useState } from 'react'
import {
  Link,
  useLocation,
  useNavigate,
} from 'react-router-dom'

import { useAuth } from '../../auth/useAuth'
import { ApiError } from '../../services/api'
import { addCartItem } from '../../services/cart'
import type { ProductVariant } from '../../types/catalog'

type ProductPurchaseActionsProps = {
  variant: ProductVariant | undefined
}

export function ProductPurchaseActions({
  variant,
}: ProductPurchaseActionsProps) {
  const auth = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [hasAddedItem, setHasAddedItem] = useState(false)

  async function handleAddToCart() {
    if (
      !variant
      || !variant.is_in_stock
      || auth.isLoading
    ) {
      return
    }

    if (!auth.token || !auth.isAuthenticated) {
      navigate(
        '/login',
        {
          state: {
            from: location.pathname,
          },
        },
      )

      return
    }

    try {
      setIsSubmitting(true)
      setFeedback(null)
      setHasAddedItem(false)

      await addCartItem(
        auth.token,
        {
          variant_id: variant.id,
          quantity: 1,
        },
      )

      setFeedback('Produto adicionado ao carrinho.')
      setHasAddedItem(true)
    } catch (requestError) {
      setFeedback(
        requestError instanceof ApiError
          ? requestError.message
          : 'Não foi possível adicionar o produto ao carrinho.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const isDisabled = (
    !variant
    || !variant.is_in_stock
    || auth.isLoading
    || isSubmitting
  )

  return (
    <div className="product-purchase">
      <button
        className="button-primary product-purchase__button"
        disabled={isDisabled}
        type="button"
        onClick={() => {
          void handleAddToCart()
        }}
      >
        {isSubmitting
          ? 'Adicionando...'
          : 'Adicionar ao carrinho'}
      </button>

      {!variant?.is_in_stock && (
        <p className="product-purchase__feedback">
          Selecione uma variação disponível.
        </p>
      )}

      {feedback && (
        <p
          className="product-purchase__feedback"
          role="status"
        >
          {feedback}
        </p>
      )}

      {hasAddedItem && (
        <Link
          className="product-purchase__cart-link"
          to="/carrinho"
        >
          Ver carrinho
        </Link>
      )}
    </div>
  )
}
