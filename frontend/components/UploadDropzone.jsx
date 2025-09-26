"use client";

import { useCallback, useRef, useState } from "react";
import * as XLSX from "xlsx";
import Papa from "papaparse";
import { UploadCloud } from "lucide-react";

export default function UploadDropzone({ onDataParsed }) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);
  const [error, setError] = useState("");

  const parseWorkbook = (wb, fileMeta) => {
    const sheets = {};
    wb.SheetNames.forEach((name) => {
      const json = XLSX.utils.sheet_to_json(wb.Sheets[name], { header: 1 });
      sheets[name] = json;
    });
    const first = wb.SheetNames[0];
    onDataParsed({ sheets, active: first, fileMeta });
  };

  const handleFiles = useCallback(
    async (file) => {
      setError("");
      if (!file) return;
      const ext = file.name.toLowerCase().split(".").pop();

      // First: upload raw file to backend to obtain persisted URL
      let uploadedUrl = null;
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data?.url) {
          uploadedUrl = data.url;
          console.log("✅ Remote file uploaded:", uploadedUrl);
        } else if (data?.error) {
          console.warn("Remote upload failed:", data.error);
        }
      } catch (e) {
        console.warn("Remote upload request error", e);
      }

      const fileMeta = {
        name: file.name,
        size: file.size,
        type: file.type,
        url: uploadedUrl,
      };

      if (ext === "xlsx" || ext === "xls") {
        const reader = new FileReader();
        reader.onload = (e) => {
          const dataArr = new Uint8Array(e.target.result);
          const wb = XLSX.read(dataArr, { type: "array" });
          parseWorkbook(wb, fileMeta);
        };
        reader.readAsArrayBuffer(file);
      } else if (ext === "csv") {
        Papa.parse(file, {
          complete: (results) => {
            onDataParsed({
              sheets: { Sheet1: results.data },
              active: "Sheet1",
              fileMeta,
            });
          },
        });
      } else {
        setError("Unsupported file type. Please upload .xlsx or .csv");
      }
    },
    [onDataParsed]
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDrag(false);
    const file = e.dataTransfer.files[0];
    handleFiles(file);
  };

  return (
    <div
      className={`upload-dropzone ${drag ? "dragover" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDrag(true);
      }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter") inputRef.current?.click();
      }}
      aria-label="Upload XLSX or CSV inventory file"
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files[0])}
      />
      <div className="flex flex-col items-center space-y-4">
        <div className="w-16 h-16 bg-white border border-gray-200 rounded-2xl flex items-center justify-center shadow-sm">
          <UploadCloud className="h-8 w-8 text-brand-emerald" />
        </div>
        <div>
          <p className="font-medium">Click or drag file to upload</p>
          <p className="text-sm text-gray-500 mt-1">
            Accepted formats: XLSX, CSV
          </p>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}
