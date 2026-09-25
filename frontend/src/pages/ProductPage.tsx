import { useParams } from 'react-router-dom'

export function ProductPage() {
  const { slug } = useParams()

  return (
    <section className="page-section">
      <div className="container">
        <p className="eyebrow">Produto</p>
        <h1>Detalhes do produto</h1>

        <p className="page-intro">
          Produto selecionado: {slug ?? 'não informado'}
        </p>
      </div>
    </section>
  )
}
