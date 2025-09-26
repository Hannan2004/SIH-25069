"use client";

import { useState, useEffect } from "react";

export default function EditableSheet({ sheetName, data, onChange }) {
  const [rows, setRows] = useState(data || []);

  useEffect(() => setRows(data), [data]);

  const updateCell = (r, c, value) => {
    const newRows = rows.map((row, ri) =>
      row.map((cell, ci) => (ri === r && ci === c ? value : cell))
    );
    setRows(newRows);
    onChange(newRows);
  };

  if (!data)
    return <p className="text-sm text-gray-500 p-4">No sheet selected.</p>;

  return (
    <div className="overflow-auto max-h-[70vh]">
      <table className="min-w-full border text-xs">
        <tbody>
          {rows.map((row, rIdx) => (
            <tr key={rIdx} className="border-b">
              {row.map((cell, cIdx) => (
                <td key={cIdx} className="border-r min-w-[120px] max-w-[240px]">
                  <div
                    className="editable-cell"
                    contentEditable
                    suppressContentEditableWarning
                    onBlur={(e) =>
                      updateCell(rIdx, cIdx, e.currentTarget.textContent)
                    }
                  >
                    {cell}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
