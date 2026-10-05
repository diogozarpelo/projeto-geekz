import {
  BrowserRouter,
  Route,
  Routes,
} from 'react-router-dom'

import { RequireAuth } from '../../auth/RequireAuth'
import { AppLayout } from '../../components/layout/AppLayout'
import { CartPage } from '../../pages/CartPage'
import { CatalogPage } from '../../pages/CatalogPage'
import { CheckoutPage } from '../../pages/CheckoutPage'
import { HomePage } from '../../pages/HomePage'
import { LoginPage } from '../../pages/LoginPage'
import { MyAccountPage } from '../../pages/MyAccountPage'
import { MyOrdersPage } from '../../pages/MyOrdersPage'
import { NotFoundPage } from '../../pages/NotFoundPage'
import { OrderPage } from '../../pages/OrderPage'
import { ProductPage } from '../../pages/ProductPage'
import { RegisterPage } from '../../pages/RegisterPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/catalogo" element={<CatalogPage />} />
          <Route path="/produto/:slug" element={<ProductPage />} />

          <Route path="/login" element={<LoginPage />} />
          <Route path="/cadastro" element={<RegisterPage />} />

          <Route
            path="/carrinho"
            element={
              <RequireAuth>
                <CartPage />
              </RequireAuth>
            }
          />

          <Route
            path="/checkout"
            element={
              <RequireAuth>
                <CheckoutPage />
              </RequireAuth>
            }
          />

          <Route
            path="/minha-conta"
            element={
              <RequireAuth>
                <MyAccountPage />
              </RequireAuth>
            }
          />
          <Route
            path="/pedidos"
            element={
              <RequireAuth>
                <MyOrdersPage />
              </RequireAuth>
            }
          />
          <Route
            path="/pedidos/:publicId"
            element={
              <RequireAuth>
                <OrderPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
