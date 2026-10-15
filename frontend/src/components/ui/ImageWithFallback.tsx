import { useState } from 'react'

interface ImageWithFallbackProps {
  src?: string | null
  alt: string
  imageClassName?: string
  fallbackClassName: string
  fallbackLabel?: string
  loading?: 'eager' | 'lazy'
}

export function ImageWithFallback({
  src,
  alt,
  imageClassName,
  fallbackClassName,
  fallbackLabel = 'Geekz',
  loading = 'lazy',
}: ImageWithFallbackProps) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null)

  if (!src || failedSrc === src) {
    return (
      <span
        className={fallbackClassName}
        aria-hidden="true"
      >
        {fallbackLabel}
      </span>
    )
  }

  return (
    <img
      className={imageClassName}
      src={src}
      alt={alt}
      loading={loading}
      onError={() => {
        setFailedSrc(src)
      }}
    />
  )
}
