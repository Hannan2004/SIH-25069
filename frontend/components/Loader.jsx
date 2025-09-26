export default function Loader({
  text = "Processing...",
  steps = [],
  currentStep = 0,
  variant = "dots", // 'dots' | 'spinner'
}) {
  const showSteps = steps.length > 0;
  return (
    <div className="flex flex-col items-center justify-center py-10">
      {variant === "spinner" && !showSteps && (
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-brand-emerald border-t-transparent mb-4" />
      )}
      {variant === "dots" && !showSteps && (
        <div className="flex space-x-2 mb-4" aria-label="Loading">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-full bg-brand-emerald animate-pulse"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      )}
      {showSteps ? (
        <div className="w-full max-w-md space-y-5">
          <div className="text-center">
            <h3 className="font-semibold text-gray-900 mb-1">Processing...</h3>
            <p className="text-sm text-gray-600">
              Step {currentStep + 1} of {steps.length}
            </p>
          </div>
          <ol className="space-y-3" aria-label="Progress steps">
            {steps.map((step, index) => {
              const state =
                index < currentStep
                  ? "done"
                  : index === currentStep
                  ? "active"
                  : "upcoming";
              return (
                <li key={index} className="flex items-center space-x-3">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-colors ${
                      state === "done"
                        ? "bg-green-100 text-green-700"
                        : state === "active"
                        ? "bg-brand-emerald text-white animate-pulse"
                        : "bg-gray-100 text-gray-400"
                    }`}
                    aria-current={state === "active" ? "step" : undefined}
                  >
                    {state === "done" ? "✓" : index + 1}
                  </div>
                  <span
                    className={`text-sm ${
                      state !== "upcoming" ? "text-gray-800" : "text-gray-400"
                    }`}
                  >
                    {step}
                  </span>
                </li>
              );
            })}
          </ol>
        </div>
      ) : (
        <p className="text-xs text-gray-500" role="status">
          {text}
        </p>
      )}
    </div>
  );
}
