import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">404</p>
        <h1>Página não encontrada</h1>

        <Link className="button-primary" to="/">
          Voltar para a Home
        </Link>
      </div>
    </section>
  )
}
