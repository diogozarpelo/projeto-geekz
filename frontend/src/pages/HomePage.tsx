import { Link } from 'react-router-dom'

export function HomePage() {
  return (
    <section className="page-section">
      <div className="container hero-section">
        <p className="eyebrow">Geekz</p>

        <h1>Vista o universo que você curte.</h1>

        <p className="page-intro">
          Camisas inspiradas em games, animes, filmes e séries.
        </p>

        <Link className="button-primary" to="/catalogo">
          Explorar catálogo
        </Link>
      </div>
    </section>
  )
}
