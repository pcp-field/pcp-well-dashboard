# Engineering inputs and limitations

## Input provenance

The supplied archive contained 56 PDFs. Four byte-identical duplicates were excluded, leaving 52 distinct well reports. The current local CSV preserves well identifiers, numeric results, liner descriptions, software versions, source filenames, PDF page numbers, and report wear notes. Report-derived data is distinct from independent field measurements.

The data contains 45 records marked `No Liner/Coating` and seven marked `HDPE Liner`. The paper's rounded descriptive results were reproduced by the existing scripts. The application does not re-extract PDFs or change the source data when filters are applied.

## Field definitions

| Input | Definition and unit | Source locator |
|---|---|---|
| `wear_rate` | Maximum Tubing Wear Rate, %/year | `wear_page` |
| `pump_speed_rpm` | Specified pump speed, RPM | `analysis_page` |
| `rod_torque_load_pct` | Maximum Rod Torque Load, % of limit; not torque in N·m | `analysis_page` |
| `rod_stress_pct` | Maximum Effective Rod Stress, % as reported | `analysis_page` |
| `produced_rate_m3_day` | Surface produced-fluid rate, m³/day | `analysis_page` |
| `max_dogleg_deg_30m` | Maximum dogleg severity, degrees per 30 m, at reported precision | `completion_page` |
| `tubing_liner_source` | Reported liner description | `completion_page` |

Page numbers are one-based PDF pages. Missing optional inputs remain unavailable; they are not replaced with zero. Only the wear, speed, well identifier, and liner fields are required for the existing calculations. Additional mechanical variables are exposed as source records, not used to invent further calculations.

## Interpretation limits

- The source set contains multiple PC-PUMP versions. The thesis statement that all results came from version 4.2 needs review.
- Some reports state a wear-rate correction factor of five. The dataset retains the final reported values and their notes. The application does not multiply or divide them again.
- Three reports contain zero calculated maximum wear. Their notes indicate model exclusions for internal wear in some guides or couplings. Zero does not establish a wear-free or safe well.
- A filename containing GRE conflicts with an HDPE liner description inside its report. The extraction follows the report body; confirm source configuration before material-specific conclusions.
- Differences in group mean wear do not isolate liner effects. Group sizes and operating speeds differ. The application displays group counts and speed means alongside wear means.
- Field context is Marmul, Nimr, and Rima. No verified row-to-field mapping was supplied, so no field filter or field-specific results are fabricated.
- PIPESIM 2023 can supplement the wider engineering project. No PIPESIM data or connection has been supplied, and none is required to run the preserved Python analysis.
- No safety thresholds, remaining-life estimates, or causal claims are generated.
