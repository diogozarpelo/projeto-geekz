import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AppLayout } from '../../components/layout/AppLayout'
import { CartPage } from '../../pages/CartPage'
import { CatalogPage } from '../../pages/CatalogPage'
import { CheckoutPage } from '../../pages/CheckoutPage'
import { HomePage } from '../../pages/HomePage'
import { NotFoundPage } from '../../pages/NotFoundPage'
import { ProductPage } from '../../pages/ProductPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/catalogo" element={<CatalogPage />} />
          <Route path="/produto/:slug" element={<ProductPage />} />
          <Route path="/carrinho" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
