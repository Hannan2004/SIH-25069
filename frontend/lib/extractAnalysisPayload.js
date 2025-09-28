import * as XLSX from "xlsx";

/** Normalize strings for matching */
export function norm(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

/** Robust number parse: tolerate commas, text, units */
function toNum(v, def = 0) {
  if (v === null || v === undefined) return def;
  if (typeof v === "number" && Number.isFinite(v)) return v;
  const s = String(v).trim();
  if (!s) return def;
  const match = s.replace(/,/g, "").match(/-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/);
  if (!match) return def;
  const n = Number(match[0]);
  return Number.isFinite(n) ? n : def;
}

/** Pick first matching column from aliases, case/space/underscore/dash insensitive */
function pick(row, aliases = []) {
  const keys = Object.keys(row || {});
  const nmap = new Map(keys.map((k) => [norm(k), k]));
  for (const a of aliases) {
    const nk = norm(a);
    if (nmap.has(nk)) return row[nmap.get(nk)];
  }
  return undefined;
}

/** Detect if sheet is key-value rows (2 columns) or header table */
function detectSheetType(rows) {
  if (!rows || !rows.length) return "unknown";
  const r0 = rows[0];
  const headers = Object.keys(r0);
  // If looks like "A", "B", etc., or exactly two columns without header names
  if (headers.some((h) => /^__EMPTY/.test(h))) return "kv";
  // If only two columns named something like "key","value"
  if (headers.length === 2 && ["key", "name"].includes(norm(headers[0])))
    return "kv";
  // If it has meaningful headers (like your LCA SHEET-1.xlsx), treat as table
  return "table";
}

/** Map from Key-Value style rows (legacy) */
export function mapFromKeyValueRows(rows) {
  // Build lookup: first col -> second col
  const lookup = {};
  for (const r of rows) {
    const cols = Object.keys(r);
    if (cols.length < 2) continue;
    const k = r[cols[0]];
    const v = r[cols[1]];
    if (k != null && k !== "") lookup[k] = v;
  }

  // Old flexible key map
  const keyMap = {
    material_type: ["materialtype", "material", "material_category"],
    mass_kg: ["masskg", "mass", "weightkg", "inputmass"],

    virgin_energy_kwh_per_kg: [
      "virginenergy",
      "virginenergykwhperkg",
      "primaryenergykwhkg",
    ],
    recycled_energy_kwh_per_kg: [
      "recycledenergy",
      "recycledenergykwhperkg",
      "secenergykwhkg",
    ],

    virgin_direct_emissions: [
      "virgindirectemissions",
      "primarydirectemissions",
      "virgindirect",
    ],
    recycled_direct_emissions: [
      "recycleddirectemissions",
      "secondarydirectemissions",
      "recycleddirect",
    ],

    coal_percent: ["coalpercent", "coalshare"],
    gas_percent: ["gaspercent", "gasshare"],
    oil_percent: ["oilpercent", "oilshare"],
    nuclear_percent: ["nuclearpercent", "nuclearshare"],
    hydro_percent: ["hydropercent", "hydroshare", "hydropowerpercent"],
    wind_percent: ["windpercent", "windshare"],
    solar_percent: ["solarpercent", "solarshare", "pvpercent"],
    other_renewable_percent: [
      "otherrenewablepercent",
      "otherrenewables",
      "otherrenewableshare",
    ],

    transport_mode: ["transportmode", "mode"],
    distance_km: ["distancekm", "distkm", "transportdistance"],
    weight_tonnes: ["weighttonnes", "weightt", "shipmentweight"],

    recycled_content_percent: [
      "recycledcontentpercent",
      "recycledcontent",
      "rcpercent",
    ],
    collection_rate_percent: ["collectionratepercent", "collectionrate"],
    recycling_efficiency_percent: [
      "recyclingefficiencypercent",
      "recyclingeffectiveness",
      "recyclingeffectivity",
    ],
  };

  const findKV = (target) => {
    const aliases = [target, ...(keyMap[target] || [])];
    for (const k of Object.keys(lookup)) {
      if (norm(k) === norm(target)) return lookup[k];
      for (const a of aliases) {
        if (norm(k) === norm(a)) return lookup[k];
      }
    }
    return undefined;
  };

  return {
    material: {
      material_type: findKV("material_type") || "aluminum",
      mass_kg: toNum(findKV("mass_kg")),
    },
    energy: {
      virgin_energy_kwh_per_kg: toNum(findKV("virgin_energy_kwh_per_kg")),
      recycled_energy_kwh_per_kg: toNum(findKV("recycled_energy_kwh_per_kg")),
    },
    emissions: {
      virgin_direct_emissions: toNum(findKV("virgin_direct_emissions")),
      recycled_direct_emissions: toNum(findKV("recycled_direct_emissions")),
    },
    grid_composition: {
      coal_percent: toNum(findKV("coal_percent")),
      gas_percent: toNum(findKV("gas_percent")),
      oil_percent: toNum(findKV("oil_percent")),
      nuclear_percent: toNum(findKV("nuclear_percent")),
      hydro_percent: toNum(findKV("hydro_percent")),
      wind_percent: toNum(findKV("wind_percent")),
      solar_percent: toNum(findKV("solar_percent")),
      other_renewable_percent: toNum(findKV("other_renewable_percent")),
    },
    transport: {
      transport_mode: String(findKV("transport_mode") || "truck"),
      distance_km: toNum(findKV("distance_km")),
      weight_tonnes: toNum(findKV("weight_tonnes")),
    },
    recycling: {
      recycled_content_percent: toNum(findKV("recycled_content_percent")),
      collection_rate_percent: toNum(findKV("collection_rate_percent")),
      recycling_efficiency_percent: toNum(
        findKV("recycling_efficiency_percent")
      ),
    },
    analysis_type: "cradle_to_gate",
    report_format: "json",
  };
}

/** Map from header table rows (preferred) — tailored to LCA SHEET-1.xlsx */
export function mapFromHeaderTable(rows) {
  if (!Array.isArray(rows)) rows = [];
  const cleaned = rows.filter(
    (r) =>
      r &&
      Object.values(r).some((v) => v !== "" && v !== null && v !== undefined)
  );
  if (!cleaned.length) cleaned.push({});
  const numericKeysCandidate = [
    "Mass_kg",
    "EI_process",
    "EI_recycled",
    "EF_direct",
    "EF_direct_recycled",
    "Coal_pct",
    "Gas_pct",
    "Oil_pct",
    "Nuclear_pct",
    "Hydro_pct",
    "Wind_pct",
    "Solar_pct",
    "Other_pct",
    "Transport_distance_km",
    "Transport_weight_t",
    "Transport_EF",
    "Virgin_EF",
    "Secondary_EF",
    "Collection_rate",
    "Recycling_efficiency",
    "Secondary_content_existing",
  ];
  const scoreRow = (r) => {
    let score = 0;
    const materialVal = pick(r, ["Material", "material", "Material_type"]);
    if (materialVal) score += 5;
    for (const k of Object.keys(r)) {
      const nk = norm(k);
      if (numericKeysCandidate.some((c) => norm(c) === nk)) {
        const val = toNum(r[k], NaN);
        if (!Number.isNaN(val) && val !== 0) score += 1;
      }
    }
    return score;
  };
  const best =
    cleaned.reduce((best, cur) => {
      const sc = scoreRow(cur);
      if (!best || sc > best.__score)
        return Object.assign({}, cur, { __score: sc });
      return best;
    }, null) || {};
  const row = { ...best };
  delete row.__score;

  const material_type = pick(row, ["Material", "Material_type", "material"]);
  const mass_kg = toNum(pick(row, ["Mass_kg", "Mass (kg)", "Mass", "mass_kg"]));
  const virgin_energy_kwh_per_kg = toNum(
    pick(row, [
      "EI_process",
      "Virgin_EI",
      "Primary_EI",
      "Virgin_energy",
      "Virgin_kWh_per_kg",
    ])
  );
  const recycled_energy_kwh_per_kg = toNum(
    pick(row, [
      "EI_recycled",
      "Secondary_EI",
      "Recycled_energy",
      "Recycled_kWh_per_kg",
    ])
  );
  const virgin_direct_emissions = toNum(
    pick(row, ["EF_direct", "Virgin_EF", "Virgin_direct", "Virgin_emissions"])
  );
  const recycled_direct_emissions = toNum(
    pick(row, [
      "EF_direct_recycled",
      "Secondary_EF",
      "Recycled_direct",
      "Recycled_emissions",
    ])
  );

  const grid_composition = {
    coal_percent: toNum(pick(row, ["Coal_pct", "Coal%", "Coal"])),
    gas_percent: toNum(pick(row, ["Gas_pct", "Gas%", "Gas"])),
    oil_percent: toNum(pick(row, ["Oil_pct", "Oil%", "Oil"])),
    nuclear_percent: toNum(pick(row, ["Nuclear_pct", "Nuclear%", "Nuclear"])),
    hydro_percent: toNum(
      pick(row, ["Hydro_pct", "Hydro%", "Hydro", "Hydro_power"])
    ),
    wind_percent: toNum(pick(row, ["Wind_pct", "Wind%", "Wind"])),
    solar_percent: toNum(pick(row, ["Solar_pct", "Solar%", "Solar", "PV"])),
    other_renewable_percent: toNum(
      pick(row, ["Other_pct", "Other%", "Other", "Other_renewable"])
    ),
  };

  const transport = {
    transport_mode: String(pick(row, ["Transport_mode", "Mode"]) || "truck"),
    distance_km: toNum(
      pick(row, [
        "Transport_distance_km",
        "Distance_km",
        "Transport_km",
        "Distance",
      ])
    ),
    weight_tonnes: toNum(
      pick(row, ["Transport_weight_t", "Weight_t", "Shipment_t"])
    ),
    transport_emission_factor: toNum(
      pick(row, [
        "Transport_EF",
        "Transport_emission_factor",
        "Transport_EF_kgCO2e_tkm",
      ])
    ),
  };

  const recycling = {
    recycled_content_percent: toNum(
      pick(row, [
        "Secondary_content_existing",
        "Recycled_content_percent",
        "RC_percent",
        "Recycled_content",
        "Recycled%",
      ])
    ),
    collection_rate_percent: toNum(
      pick(row, ["Collection_rate", "Collection_rate_percent", "Collection%"])
    ),
    recycling_efficiency_percent: toNum(
      pick(row, [
        "Recycling_efficiency",
        "Recycling_efficiency_percent",
        "Recycling_eff%",
      ])
    ),
  };

  let payload = {
    material: {
      material_type:
        (material_type && String(material_type).trim()) || "aluminum",
      mass_kg,
    },
    energy: { virgin_energy_kwh_per_kg, recycled_energy_kwh_per_kg },
    emissions: { virgin_direct_emissions, recycled_direct_emissions },
    grid_composition,
    transport,
    recycling,
    analysis_type: "cradle_to_gate",
    report_format: "json",
  };

  const baseAllZero =
    !payload.material.mass_kg &&
    !virgin_energy_kwh_per_kg &&
    !recycled_energy_kwh_per_kg &&
    !virgin_direct_emissions &&
    !recycled_direct_emissions;
  if (baseAllZero && cleaned.length > 1) {
    const altRow = cleaned.filter((r) => r !== row)[0];
    if (altRow) {
      try {
        const alt = mapFromHeaderTable([altRow]);
        if (alt.material.mass_kg) payload = alt;
      } catch {}
    }
  }
  return payload;
}

/** Entry point: parse XLSX buffer and produce payload */
export function extractAnalysisPayloadFromXlsx(fileBuffer, options = {}) {
  const wb = XLSX.read(fileBuffer, { type: "buffer" });
  const name = (wb.SheetNames && wb.SheetNames[0]) || "Sheet1";
  const ws = wb.Sheets[name];
  const rows = XLSX.utils.sheet_to_json(ws, { defval: "" });

  const mode = detectSheetType(rows);

  if (mode === "table") {
    return mapFromHeaderTable(rows);
  }
  if (mode === "kv") {
    return mapFromKeyValueRows(rows);
  }
  // Fallback: try table mapping anyway
  return mapFromHeaderTable(rows);
}

// Backwards compatibility: allow existing code that passes a 2D array of rows (headerless key/value pairs)
// or an array-of-arrays representing [key,value]. If first element is an array, map to objects like {key:..., value:...}
export function extractAnalysisPayload(rows) {
  if (!Array.isArray(rows) || !rows.length) return mapFromKeyValueRows([]);

  // Case A: header:1 2D raw arrays (first row = headers)
  if (Array.isArray(rows[0])) {
    // If first row contains more than 2 columns -> treat as a header table
    const headerRow = rows[0];
    const dataRows = rows.slice(1).filter((r) => Array.isArray(r));
    const nonEmptyHeaderCount = headerRow.filter(
      (h) => h !== null && h !== undefined && h !== ""
    ).length;
    if (nonEmptyHeaderCount > 2) {
      // Build objects
      const objects = dataRows
        .map((r) => {
          const obj = {};
          headerRow.forEach((h, idx) => {
            if (!h && h !== 0) return;
            obj[String(h)] = r[idx];
          });
          return obj;
        })
        .filter((o) => Object.keys(o).length);
      if (objects.length) return mapFromHeaderTable(objects);
    }
    // Otherwise assume key-value pairs: each subsequent row [key,value]
    const kvObjects = dataRows
      .filter((r) => r.length >= 2 && r[0] != null && r[0] !== "")
      .map((r) => ({ KEY: r[0], VALUE: r[1] }));
    return mapFromKeyValueRows(kvObjects);
  }

  // Case B: already array of objects
  if (typeof rows[0] === "object" && !Array.isArray(rows[0])) {
    const mode = detectSheetType(rows);
    if (mode === "table") return mapFromHeaderTable(rows);
    return mapFromKeyValueRows(rows);
  }
  return mapFromKeyValueRows([]);
}

// Optional helper: validate payload (can be surfaced in UI)
export function validatePayload(payload) {
  const issues = [];
  if (!payload.material.mass_kg) issues.push("mass_kg is 0 or missing");
  const grid = payload.grid_composition || {};
  const gridSum = [
    "coal_percent",
    "gas_percent",
    "oil_percent",
    "nuclear_percent",
    "hydro_percent",
    "wind_percent",
    "solar_percent",
    "other_renewable_percent",
  ]
    .map((k) => Number(grid[k] || 0))
    .reduce((a, b) => a + b, 0);
  if (gridSum && (gridSum < 95 || gridSum > 105))
    issues.push("grid composition does not sum ~100%");
  return { valid: issues.length === 0, issues };
}
