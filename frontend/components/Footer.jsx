import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="bg-brand-blue border-t border-brand-blue/70 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <span className="w-12 h-12 rounded-full bg-white shadow flex items-center justify-center ring-1 ring-white/40 overflow-hidden">
                <Image
                  src="/DhatuChakr-logo.png"
                  width={48}
                  height={48}
                  alt="DhatuChakr Logo"
                  className="object-contain"
                  priority
                />
              </span>
              <span className="font-bold text-xl text-white">DhatuChakr</span>
            </div>
            <p className="text-white/80 max-w-md leading-relaxed">
              India's first AI-assisted Life Cycle Assessment platform for
              metals and critical minerals. Built for compliance, designed for
              circularity.
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-semibold text-white mb-4">Product</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/goal-scope"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  Goal & Scope
                </Link>
              </li>
              <li>
                <Link
                  href="/projects/new"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  New Analysis
                </Link>
              </li>
              <li>
                <Link
                  href="#"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  Documentation
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="font-semibold text-white mb-4">Company</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="#"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  About
                </Link>
              </li>
              <li>
                <Link
                  href="#"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link
                  href="#"
                  className="relative text-white/80 hover:text-white transition-colors after:absolute after:left-0 after:bottom-0 after:h-0.5 after:w-0 hover:after:w-full after:bg-brand-copper after:transition-all"
                >
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/10">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-white/60 text-sm">
              © 2025 DhatuChakr. All rights reserved.
            </p>
            <p className="text-white/60 text-sm mt-2 md:mt-0">
              ISO 14040/44 compliant • EPD-ready • Made in India
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
