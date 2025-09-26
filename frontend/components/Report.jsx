export default function Report({
  project,
  stats,
  recommendations,
  comparisonData,
}) {
  return (
    <div className="hidden print:block p-8 text-sm">
      <h1 className="text-3xl font-bold mb-2">DhatuChakr Report</h1>
      {project && <p className="mb-4">Project: {project.projectName}</p>}
      <h2 className="text-xl font-semibold mb-2">Key Performance Indicators</h2>
      <ul className="grid grid-cols-2 gap-2 mb-6">
        {stats.map((s, i) => (
          <li key={i} className="p-2 border rounded">
            {s.label}: <strong>{s.value}</strong>
          </li>
        ))}
      </ul>
      <h2 className="text-xl font-semibold mb-2">Recommendations</h2>
      <ol className="list-decimal pl-5 mb-6">
        {recommendations.map((r, i) => (
          <li key={i} className="mb-1">
            {r}
          </li>
        ))}
      </ol>
      <p className="text-xs text-gray-500">
        Generated via preliminary placeholder engine. Not for external
        disclosure.
      </p>
    </div>
  );
}
