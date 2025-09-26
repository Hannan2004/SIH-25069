import Link from 'next/link'
import { ArrowRight, Database, Cpu, Award, Recycle, Zap, FileSpreadsheet, ChartBar as BarChart3, Download } from 'lucide-react'
import PageHero from '@/components/PageHero'
import Section from '@/components/Section'
import Card from '@/components/Card'
import FeatureIcon from '@/components/FeatureIcon'
import Button from '@/components/Button'

export default function Home() {
  const usps = [
    {
      icon: Database,
      title: "India-Calibrated Datasets",
      description: "Grid mix, transport patterns, and scrap flows tailored for Indian industrial conditions"
    },
    {
      icon: Cpu,
      title: "AI Gap Filling",
      description: "Machine learning for parameter estimation and document extraction from technical reports"
    },
    {
      icon: Award,
      title: "Compliance-First",
      description: "ISO 14040/44 methodology with EPD-ready outputs for regulatory submission"
    },
    {
      icon: Recycle,
      title: "Circularity Metrics",
      description: "Track recycled content, end-of-life rates, and closed-loop material flows"
    }
  ]

  const features = [
    {
      icon: FileSpreadsheet,
      title: "Upload & Edit",
      description: "XLSX/CSV import with inline editing and ML-assisted gap filling"
    },
    {
      icon: BarChart3,
      title: "Scenario Comparison",
      description: "Compare conventional vs circular pathways with detailed impact analysis"
    },
    {
      icon: Download,
      title: "Report Generation",
      description: "Professional PDF reports with Sankey diagrams and compliance documentation"
    }
  ]

  const metals = [
    {
      name: "Aluminium",
      symbol: "Al",
      color: "brand-aluminum",
      description: "Primary & secondary production pathways"
    },
    {
      name: "Copper", 
      symbol: "Cu",
      color: "brand-copper",
      description: "Smelting, refining, and recycling routes"
    },
    {
      name: "Critical Minerals",
      symbol: "CM",
      color: "brand-steel", 
      description: "Lithium, cobalt, rare earth elements"
    }
  ]

  return (
    <>
      <PageHero
        title="AI-Assisted Life Cycle Assessment for Aluminium, Copper & Critical Minerals"
        description="India's first comprehensive LCA platform with AI-powered gap filling, compliance-ready reporting, and circularity insights for the metals industry."
      >
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link href="/projects/new">
            <Button size="lg" className="group">
              Get Started
              <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
          <Link href="/goal-scope">
            <Button variant="outline" size="lg">
              View Goal & Scope
            </Button>
          </Link>
        </div>
      </PageHero>

      <Section>
        <div className="text-center mb-16">
          <h2 className="mb-6">Why DhatuChakr?</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Built specifically for India's metals industry with localized data, AI-powered analysis, 
            and compliance-ready outputs that meet international standards.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {usps.map((usp, index) => (
            <Card key={index} className="text-center hover:scale-105 transition-transform">
              <FeatureIcon icon={usp.icon} className="mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-3">{usp.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{usp.description}</p>
            </Card>
          ))}
        </div>
      </Section>

      <Section background="gray">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="mb-6">Complete LCA Lifecycle Coverage</h2>
            <p className="text-gray-600 mb-8 leading-relaxed">
              From mining to casting, our platform covers the entire value chain with 
              detailed process modeling and impact assessment at each stage.
            </p>
            
            <div className="space-y-4">
              {['Mining & Extraction', 'Refining & Processing', 'Smelting & Production', 'Casting & Forming', 'Transport & Logistics'].map((stage, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-brand-emerald rounded-full"></div>
                  <span className="text-gray-700">{stage}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {metals.map((metal, index) => (
              <Card key={index} className="text-center">
                <div className={`w-16 h-16 rounded-full bg-${metal.color}/20 flex items-center justify-center mx-auto mb-4`}>
                  <span className={`text-2xl font-bold text-${metal.color === 'brand-aluminum' ? 'brand-steel' : metal.color}`}>
                    {metal.symbol}
                  </span>
                </div>
                <h3 className="font-semibold mb-2">{metal.name}</h3>
                <p className="text-sm text-gray-600">{metal.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </Section>

      <Section>
        <div className="text-center mb-16">
          <h2 className="mb-6">India-First Database</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            All defaults calibrated for Indian conditions - electricity grid mix, 
            transport patterns, and recycling infrastructure - but fully customizable for your specific operations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="text-center">
            <FeatureIcon icon={Zap} color="accent-sun" className="mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-3">Grid Electricity</h3>
            <p className="text-gray-600 text-sm">State-wise grid factors with renewable energy integration scenarios</p>
          </Card>

          <Card className="text-center">
            <FeatureIcon icon={Database} color="brand-copper" className="mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-3">Transport Networks</h3>
            <p className="text-gray-600 text-sm">Road vs rail optimization with Indian logistics cost and emission factors</p>
          </Card>

          <Card className="text-center">
            <FeatureIcon icon={Recycle} color="brand-emerald" className="mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-3">Scrap & Recycling</h3>
            <p className="text-gray-600 text-sm">Domestic scrap availability, collection rates, and processing efficiency</p>
          </Card>
        </div>
      </Section>

      <Section background="gray">
        <div className="text-center mb-16">
          <h2 className="mb-6">Powerful Features</h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            From data upload to final reporting, every step is designed for efficiency and accuracy.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card key={index} className="text-center">
              <FeatureIcon icon={feature.icon} size="lg" className="mx-auto mb-6" />
              <h3 className="text-xl font-semibold mb-4">{feature.title}</h3>
              <p className="text-gray-600 leading-relaxed">{feature.description}</p>
            </Card>
          ))}
        </div>
      </Section>

      <Section>
        <div className="text-center mb-16">
          <h2 className="mb-6">Trusted by Industry Leaders</h2>
          <p className="text-gray-600 mb-8">
            Join companies across the metals value chain using DhatuChakr for compliance and sustainability reporting
          </p>
          
          {/* Placeholder logos */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center opacity-60">
            {[1,2,3,4].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                <span className="text-gray-400 text-sm">Partner {i}</span>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section background="gradient" className="text-center">
        <h2 className="mb-6">Ready to Start Your LCA Analysis?</h2>
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto leading-relaxed">
          Join the sustainable metals revolution with AI-powered insights and India-first data.
        </p>
        <Link href="/projects/new">
          <Button size="lg" className="group">
            Start Your First Analysis
            <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
          </Button>
        </Link>
      </Section>
    </>
  )
}