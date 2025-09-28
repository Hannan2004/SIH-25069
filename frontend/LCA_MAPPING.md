# LCA Excel -> API Payload Mapping

This document explains how spreadsheet headers are mapped into the nested JSON body sent to the backend `/analyze/comprehensive` endpoint.

## Final Payload Shape

```json
{
  "material": { "material_type": "steel", "mass_kg": 150 },
  "energy": {
    "virgin_energy_kwh_per_kg": 6.0,
    "recycled_energy_kwh_per_kg": 2.5
  },
  "emissions": {
    "virgin_direct_emissions": 2.3,
    "recycled_direct_emissions": 0.5
  },
  "grid_composition": {
    "coal_percent": 30,
    "gas_percent": 30,
    "oil_percent": 10,
    "nuclear_percent": 10,
    "hydro_percent": 10,
    "wind_percent": 5,
    "solar_percent": 3,
    "other_renewable_percent": 2
  },
  "transport": {
    "transport_mode": "truck",
    "distance_km": 500,
    "weight_tonnes": 0.15
  },
  "recycling": {
    "recycled_content_percent": 40,
    "collection_rate_percent": 75,
    "recycling_efficiency_percent": 90
  },
  "analysis_type": "cradle_to_gate",
  "report_format": "json"
}
```

## Header Extraction Logic

The function `findValue(sheets, headerCandidates, fallback)` scans every sheet:

1. Uses first row as header row (case-insensitive).
2. For the first matching header, scans down the column for the first numeric cell.
3. Returns fallback if nothing found.

## Mapping Table

| Payload Field                            | Header Candidates (case-insensitive)                                         | Fallback  |
| ---------------------------------------- | ---------------------------------------------------------------------------- | --------- |
| material.material_type                   | (from project metadata; no direct header yet)                                | `"steel"` |
| material.mass_kg                         | `mass`, `mass_kg`, `quantity`                                                | 100       |
| energy.virgin_energy_kwh_per_kg          | `virgin_energy`, `ei_process`, `virgin_kwh_per_kg`                           | 6.0       |
| energy.recycled_energy_kwh_per_kg        | `recycled_energy`, `ei_recycled`, `recycled_kwh_per_kg`                      | 2.5       |
| emissions.virgin_direct_emissions        | `virgin_direct_emissions`, `ef_direct`, `direct_virgin`                      | 2.3       |
| emissions.recycled_direct_emissions      | `recycled_direct_emissions`, `ef_direct_recycled`, `direct_recycled`         | 0.5       |
| grid_composition.coal_percent            | `coal_pct`, `coal`, `coal_percent`                                           | 30        |
| grid_composition.gas_percent             | `gas_pct`, `gas`, `gas_percent`                                              | 30        |
| grid_composition.oil_percent             | `oil_pct`, `oil`, `oil_percent`                                              | 10        |
| grid_composition.nuclear_percent         | `nuclear_pct`, `nuclear`, `nuclear_percent`                                  | 10        |
| grid_composition.hydro_percent           | `hydro_pct`, `hydro`, `hydro_percent`                                        | 10        |
| grid_composition.wind_percent            | `wind_pct`, `wind`, `wind_percent`                                           | 5         |
| grid_composition.solar_percent           | `solar_pct`, `solar`, `solar_percent`                                        | 3         |
| grid_composition.other_renewable_percent | `other_pct`, `other`, `other_renewable_percent`                              | 2         |
| transport.distance_km                    | `transport_distance_km`, `distance`, `distance_km`                           | 500       |
| recycling.recycled_content_percent       | `secondary_content_existing`, `recycled_content`, `recycled_content_percent` | 40        |
| recycling.collection_rate_percent        | `collection_rate`, `collection_rate_percent`                                 | 75        |
| recycling.recycling_efficiency_percent   | `recycling_efficiency`, `recycling_efficiency_percent`                       | 90        |

Transport mode is inferred: `ship` if distance > 1200 km else `truck` (can be enhanced later).
Weight (tonnes) = `mass_kg / 1000`.

## Future Enhancements

- Support explicit headers for transport mode & weight.
- Allow user override of inferred defaults via UI before submission.
- Data quality scoring per column.

---

# LCA Spreadsheet Header Mapping (Updated)

This document maps spreadsheet column headers (including legacy capitalized forms) to the nested JSON payload expected by the backend `/analyze/comprehensive` endpoint.

## Material

| Payload Field          | Accepted Headers (case-insensitive) | Notes                     |
| ---------------------- | ----------------------------------- | ------------------------- |
| material.material_type | Material                            | First non-empty cell used |
| material.mass_kg       | Mass, Mass_kg, Mass (kg)            | Defaults 100 if missing   |

## Energy (Process Energy Intensity)

| Payload Field                     | Accepted Headers                                  | Notes       |
| --------------------------------- | ------------------------------------------------- | ----------- |
| energy.virgin_energy_kwh_per_kg   | virgin_energy, EI_process, virgin_kwh_per_kg      | Default 6.0 |
| energy.recycled_energy_kwh_per_kg | recycled_energy, EI_recycled, recycled_kwh_per_kg | Default 2.5 |

## Direct Emissions Factors

| Payload Field                       | Accepted Headers                                               | Notes                                                         |
| ----------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------- |
| emissions.virgin_direct_emissions   | virgin_direct_emissions, EF_direct, direct_virgin              | Default 2.3                                                   |
| emissions.recycled_direct_emissions | recycled_direct_emissions, EF_direct_recycled, direct_recycled | Default 0.5                                                   |
| (extras) Virgin_EF                  | virgin_ef                                                      | Stored in project.\_extractedFactors. Not currently injected. |
| (extras) Secondary_EF               | secondary_ef                                                   | Same as above.                                                |

## Grid Composition (%)

| Payload Field                            | Accepted Headers                          | Default |
| ---------------------------------------- | ----------------------------------------- | ------- |
| grid_composition.coal_percent            | coal_pct, coal, coal_percent              | 30      |
| grid_composition.gas_percent             | gas_pct, gas, gas_percent                 | 30      |
| grid_composition.oil_percent             | oil_pct, oil, oil_percent                 | 10      |
| grid_composition.nuclear_percent         | nuclear_pct, nuclear, nuclear_percent     | 10      |
| grid_composition.hydro_percent           | hydro_pct, hydro, hydro_percent           | 10      |
| grid_composition.wind_percent            | wind_pct, wind, wind_percent              | 5       |
| grid_composition.solar_percent           | solar_pct, solar, solar_percent           | 3       |
| grid_composition.other_renewable_percent | other_pct, other, other_renewable_percent | 2       |

## Transport

| Payload Field                      | Accepted Headers                             | Notes                                                            |
| ---------------------------------- | -------------------------------------------- | ---------------------------------------------------------------- |
| transport.transport_mode           | Transport_mode                               | Normalized to truck/ship/rail/air; fallback heuristic (distance) |
| transport.distance_km              | transport_distance_km, distance, distance_km | Default 500                                                      |
| transport.weight_tonnes            | transport_weight_t, weight_t, weight_tonnes  | Default mass_kg / 1000                                           |
| transport.emission_factor_override | transport_ef, transport_emission_factor      | Overrides automatic factor                                       |

Normalization Rules:

- Values containing 'road' or 'truck' -> truck
- Contains 'ship' -> ship
- Contains 'rail' -> rail
- Contains 'air' -> air
- Otherwise ship if distance > 1200 else truck

## Recycling & Circularity

| Payload Field                          | Accepted Headers                                                       | Default |
| -------------------------------------- | ---------------------------------------------------------------------- | ------- |
| recycling.recycled_content_percent     | secondary_content_existing, recycled_content, recycled_content_percent | 40      |
| recycling.collection_rate_percent      | collection_rate, collection_rate_percent                               | 75      |
| recycling.recycling_efficiency_percent | recycling_efficiency, recycling_efficiency_percent                     | 90      |

## Always Added Fields

| Field         | Value          |
| ------------- | -------------- |
| analysis_type | cradle_to_gate |
| report_format | json           |

## Future Extensions

- Potential injection of Virgin_EF and Secondary_EF into an extended payload section if backend adds support.
- Multi-material rows & aggregation.

## Debug Extras

When present, the following are stored (not sent) on the project object under `_extractedFactors`:

```
{ virginEF, secondaryEF, transportEF }
```

These can be surfaced in UI for transparency.

---

Maintainers: Update this file whenever mapping logic in `missing-values/page.jsx` changes.
