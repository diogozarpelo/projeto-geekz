import { NavLink } from 'react-router-dom'

function navClassName({ isActive }: { isActive: boolean }) {
  return isActive ? 'active' : undefined
}

export function Header() {
  return (
    <header className="site-header">
      <div className="container site-header__content">
        <NavLink className="brand" to="/">
          Geekz
        </NavLink>

        <nav className="site-nav" aria-label="Navegação principal">
          <NavLink className={navClassName} end to="/">
            Home
          </NavLink>

          <NavLink className={navClassName} to="/catalogo">
            Catálogo
          </NavLink>

          <NavLink className={navClassName} to="/carrinho">
            Carrinho
          </NavLink>
        </nav>
      </div>
    </header>
  )
}
