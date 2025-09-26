import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-brand-emerald to-brand-forest rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">DC</span>
              </div>
              <span className="font-bold text-xl text-gray-900">DhatuChakr</span>
            </div>
            <p className="text-gray-600 max-w-md leading-relaxed">
              India's first AI-assisted Life Cycle Assessment platform for metals and critical minerals. 
              Built for compliance, designed for circularity.
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Product</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/goal-scope" className="text-gray-600 hover:text-brand-emerald transition-colors">
                  Goal & Scope
                </Link>
              </li>
              <li>
                <Link href="/projects/new" className="text-gray-600 hover:text-brand-emerald transition-colors">
                  New Analysis
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-600 hover:text-brand-emerald transition-colors">
                  Documentation
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Company</h3>
            <ul className="space-y-2">
              <li>
                <Link href="#" className="text-gray-600 hover:text-brand-emerald transition-colors">
                  About
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-600 hover:text-brand-emerald transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="#" className="text-gray-600 hover:text-brand-emerald transition-colors">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 text-sm">
              © 2025 DhatuChakr. All rights reserved.
            </p>
            <p className="text-gray-500 text-sm mt-2 md:mt-0">
              ISO 14040/44 compliant • EPD-ready • Made in India
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}