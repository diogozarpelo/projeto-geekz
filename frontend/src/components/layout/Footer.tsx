import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__content">
        <div className="site-footer__brand">
          <Link className="site-footer__logo" to="/">
            Geekz
          </Link>

          <p>
            Games, animes, filmes e séries para vestir
            o universo que você curte.
          </p>
        </div>

        <nav
          className="site-footer__nav"
          aria-label="Navegação do rodapé"
        >
          <Link to="/">
            Home
          </Link>

          <Link to="/catalogo">
            Catálogo
          </Link>

          <Link to="/carrinho">
            Carrinho
          </Link>

          <Link to="/minha-conta">
            Minha conta
          </Link>
        </nav>
      </div>

      <div className="container site-footer__bottom">
        <p>
          © {new Date().getFullYear()} Geekz.
          Projeto de loja virtual.
        </p>
      </div>
    </footer>
  )
}
