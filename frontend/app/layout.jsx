import './globals.css'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'

export const metadata = {
  title: 'DhatuChakr - AI-Assisted LCA for Metals',
  description: 'India-first Life Cycle Assessment platform for Aluminium, Copper & Critical Minerals with AI-powered gap filling and compliance-ready reporting.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}