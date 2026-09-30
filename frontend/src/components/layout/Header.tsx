import { NavLink } from 'react-router-dom'

import { useAuth } from '../../auth/useAuth'

function navClassName({
  isActive,
}: {
  isActive: boolean
}) {
  return isActive ? 'active' : undefined
}

export function Header() {
  const auth = useAuth()

  return (
    <header className="site-header">
      <div className="container site-header__content">
        <NavLink className="brand" to="/">
          Geekz
        </NavLink>

        <nav
          className="site-nav"
          aria-label="Navegação principal"
        >
          <NavLink className={navClassName} end to="/">
            Home
          </NavLink>

          <NavLink className={navClassName} to="/catalogo">
            Catálogo
          </NavLink>

          <NavLink className={navClassName} to="/carrinho">
            Carrinho
          </NavLink>

          {auth.isAuthenticated ? (
            <>
              <NavLink
                className={navClassName}
                to="/pedidos"
              >
                Meus pedidos
              </NavLink>

              <span className="site-nav__user">
                {auth.user?.first_name
                  || auth.user?.email}
              </span>

              <button
                className="site-nav__button"
                type="button"
                onClick={() => {
                  void auth.signOut()
                }}
              >
                Sair
              </button>
            </>
          ) : (
            <>
              <NavLink
                className={navClassName}
                to="/login"
              >
                Entrar
              </NavLink>

              <NavLink
                className={navClassName}
                to="/cadastro"
              >
                Cadastro
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
