import './globals.css'

export const metadata = {
  title: 'Chatea con Clara',
  description: 'Desarrollado por ADL',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
