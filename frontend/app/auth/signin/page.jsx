'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { LogIn, Mail, Lock } from 'lucide-react'
import PageHero from '@/components/PageHero'
import Section from '@/components/Section'
import Card from '@/components/Card'
import Button from '@/components/Button'

export default function SignInPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    // Mock authentication - log form data
    console.log('Sign in attempt:', formData)

    // Simulate API call delay
    setTimeout(() => {
      // Mock successful login
      const mockUser = {
        name: 'Demo User',
        email: formData.email,
        org: 'Demo Organization'
      }
      
      localStorage.setItem('dc_user', JSON.stringify(mockUser))
      setIsLoading(false)
      router.push('/projects/new')
    }, 1000)
  }

  return (
    <>
      <PageHero
        title="Welcome Back"
        description="Sign in to your DhatuChakr account to continue your LCA analysis"
      />

      <Section>
        <div className="max-w-md mx-auto">
          <Card className="p-8">
            <div className="text-center mb-8">
              <div className="w-12 h-12 bg-brand-emerald/10 rounded-xl flex items-center justify-center mx-auto mb-4">
                <LogIn className="h-6 w-6 text-brand-emerald" />
              </div>
              <h2 className="text-2xl font-semibold">Sign In</h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="email"
                    required
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                    placeholder="your@email.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="password"
                    required
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-emerald focus:border-transparent"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-600">
                Don't have an account?{' '}
                <Link href="/auth/signup" className="text-brand-emerald hover:underline font-medium">
                  Sign up
                </Link>
              </p>
            </div>
          </Card>
        </div>
      </Section>
    </>
  )
}