export default function ProgressStep({ 
  steps = [], 
  currentStep = 0,
  className = ""
}) {
  return (
    <div className={`${className}`}>
      <div className="flex flex-col space-y-4">
        {steps.map((step, index) => (
          <div key={index} className={`progress-step ${index <= currentStep ? 'active' : ''}`}>
            <div className="flex items-center space-x-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium z-10 ${
                index < currentStep 
                  ? 'bg-brand-emerald text-white' 
                  : index === currentStep
                  ? 'bg-brand-emerald text-white'
                  : 'bg-gray-200 text-gray-500'
              }`}>
                {index < currentStep ? '✓' : index + 1}
              </div>
              <div className="flex-1">
                <h4 className={`font-medium ${
                  index <= currentStep ? 'text-gray-900' : 'text-gray-500'
                }`}>
                  {step.title}
                </h4>
                {step.description && (
                  <p className={`text-sm mt-1 ${
                    index <= currentStep ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    {step.description}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}