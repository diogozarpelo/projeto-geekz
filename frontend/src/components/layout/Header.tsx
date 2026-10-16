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
      <a className="skip-link" href="#main-content">
        Pular para o conteúdo
      </a>

      <div className="container site-header__content">
        <NavLink
          className="brand"
          to="/"
          aria-label="Geekz - página inicial"
        >
          <span className="brand__word">
            geek<span className="brand__z">Z</span>
          </span>
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
                to="/minha-conta"
              >
                Minha conta
              </NavLink>
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
