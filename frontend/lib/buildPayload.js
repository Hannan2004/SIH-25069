// Shared payload builder for LCA comprehensive analysis
// Accepts a project-like object containing either sheetJSON or a plain { sheets } structure.
// Exports: buildPayloadFromSheets(sheets)

function findNumericFromSheets(sheets, headerCandidates, fallback = 0) {
  const headers = headerCandidates.map((h) => h.toLowerCase());
  for (const sheetName of Object.keys(sheets || {})) {
    const rows = sheets[sheetName];
    if (!Array.isArray(rows) || rows.length === 0) continue;
    const headerRow = rows[0].map((x) =>
      (x || "").toString().trim().toLowerCase()
    );
    for (let ci = 0; ci < headerRow.length; ci++) {
      if (headers.includes(headerRow[ci])) {
        for (let r = 1; r < rows.length; r++) {
          const raw = rows[r][ci];
          if (raw !== undefined && raw !== null && raw !== "") {
            const num = Number(raw);
            if (!isNaN(num)) return num;
          }
        }
      }
    }
  }
  return fallback;
}

function extractFirstString(sheets, header) {
  for (const sheetName of Object.keys(sheets || {})) {
    const rows = sheets[sheetName];
    if (!rows?.length) continue;
    const headerRow = rows[0].map((x) =>
      (x || "").toString().trim().toLowerCase()
    );
    const idx = headerRow.indexOf(header.toLowerCase());
    if (idx !== -1) {
      for (let r = 1; r < rows.length; r++) {
        const cell = rows[r][idx];
        if (cell) return cell.toString();
      }
    }
  }
  return null;
}

export function buildPayloadFromSheets({ sheets, materialFallback = "steel" }) {
  let materialType = extractFirstString(sheets, "material") || materialFallback;

  const massKg = findNumericFromSheets(
    sheets,
    ["mass", "mass_kg", "mass (kg)"],
    100
  );
  const virginEnergy = findNumericFromSheets(
    sheets,
    ["virgin_energy", "ei_process", "virgin_kwh_per_kg"],
    6.0
  );
  const recycledEnergy = findNumericFromSheets(
    sheets,
    ["recycled_energy", "ei_recycled", "recycled_kwh_per_kg"],
    2.5
  );
  const virginDirect = findNumericFromSheets(
    sheets,
    ["virgin_direct_emissions", "ef_direct", "direct_virgin"],
    2.3
  );
  const recycledDirect = findNumericFromSheets(
    sheets,
    ["recycled_direct_emissions", "ef_direct_recycled", "direct_recycled"],
    0.5
  );

  const coal = findNumericFromSheets(
    sheets,
    ["coal_pct", "coal", "coal_percent"],
    30
  );
  const gas = findNumericFromSheets(
    sheets,
    ["gas_pct", "gas", "gas_percent"],
    30
  );
  const oil = findNumericFromSheets(
    sheets,
    ["oil_pct", "oil", "oil_percent"],
    10
  );
  const nuclear = findNumericFromSheets(
    sheets,
    ["nuclear_pct", "nuclear", "nuclear_percent"],
    10
  );
  const hydro = findNumericFromSheets(
    sheets,
    ["hydro_pct", "hydro", "hydro_percent"],
    10
  );
  const wind = findNumericFromSheets(
    sheets,
    ["wind_pct", "wind", "wind_percent"],
    5
  );
  const solar = findNumericFromSheets(
    sheets,
    ["solar_pct", "solar", "solar_percent"],
    3
  );
  const otherRen = findNumericFromSheets(
    sheets,
    ["other_pct", "other_renewable_percent"],
    2
  );

  const distance = findNumericFromSheets(
    sheets,
    ["transport_distance_km", "distance_km", "distance"],
    500
  );
  const transportEF = findNumericFromSheets(
    sheets,
    ["transport_ef", "transport_emission_factor"],
    0.062
  );
  const recycledContent = findNumericFromSheets(
    sheets,
    [
      "secondary_content_existing",
      "recycled_content_percent",
      "recycled_content",
    ],
    40
  );
  const collectionRate = findNumericFromSheets(
    sheets,
    ["collection_rate", "collection_rate_percent"],
    75
  );
  const recyclingEff = findNumericFromSheets(
    sheets,
    ["recycling_efficiency", "recycling_efficiency_percent"],
    90
  );

  const transportModeRaw = extractFirstString(sheets, "transport_mode") || "";
  const normalizedMode = (() => {
    const raw = transportModeRaw.toLowerCase();
    if (raw.includes("road") || raw.includes("truck")) return "truck";
    if (raw.includes("ship")) return "ship";
    if (raw.includes("rail")) return "rail";
    if (raw.includes("air")) return "air";
    return distance > 1200 ? "ship" : "truck";
  })();

  const weightTonnesExplicit = findNumericFromSheets(
    sheets,
    ["transport_weight_t", "weight_t", "weight_tonnes"],
    massKg / 1000
  );

  return {
    material: { material_type: materialType, mass_kg: massKg },
    energy: {
      virgin_energy_kwh_per_kg: virginEnergy,
      recycled_energy_kwh_per_kg: recycledEnergy,
    },
    emissions: {
      virgin_direct_emissions: virginDirect,
      recycled_direct_emissions: recycledDirect,
    },
    grid_composition: {
      coal_percent: coal,
      gas_percent: gas,
      oil_percent: oil,
      nuclear_percent: nuclear,
      hydro_percent: hydro,
      wind_percent: wind,
      solar_percent: solar,
      other_renewable_percent: otherRen,
    },
    transport: {
      transport_mode: normalizedMode,
      distance_km: distance,
      weight_tonnes: weightTonnesExplicit,
      emission_factor_override: transportEF,
    },
    recycling: {
      recycled_content_percent: recycledContent,
      collection_rate_percent: collectionRate,
      recycling_efficiency_percent: recyclingEff,
    },
    analysis_type: "cradle_to_gate",
    report_format: "json",
  };
}
