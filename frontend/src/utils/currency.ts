const brlFormatter = new Intl.NumberFormat(
  'pt-BR',
  {
    style: 'currency',
    currency: 'BRL',
  },
)

export function formatCurrencyBRL(
  value: string | number,
) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) {
    return String(value)
  }

  return brlFormatter.format(amount)
}
