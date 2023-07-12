import './globals.css'

export const metadata = {
  title: 'Chatea con Linguo',
  description: 'Desarrollado por ADL',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
