export default function PageHero({ 
  title, 
  description, 
  children,
  className = ""
}) {
  return (
    <div className={`gradient-bg py-16 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-gradient mb-6">
            {title}
          </h1>
          {description && (
            <p className="text-xl text-gray-600 leading-relaxed mb-8">
              {description}
            </p>
          )}
          {children}
        </div>
      </div>
    </div>
  )
}