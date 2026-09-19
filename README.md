# PCP performance workspace

A local Python engineering application for a final-year PCP performance study in Oman, with field context from Marmul, Nimr, and Rima. It provides well rankings, tubing-liner comparisons, speed-versus-wear plots, traceable well records, and printable analysis reports. All interface text, documentation, charts, and reports are in English.

## Run on macOS

Use Python 3.11 or later (tested on Python 3.14). In the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1
```

Alternatively run `Start.command`. It creates an isolated environment and installs the pinned requirements if needed. Keep the terminal open while using the application. Press Control+C to stop. The browser address is normally `http://127.0.0.1:8501`.

GitHub stores the source code; it does not run the Python server. A phone or tablet can use the responsive interface when it can access a separately configured server. A localhost address on this Mac is not accessible from another device.

## Source inspection and preserved calculations

The original student scripts are `read_wells.py`, `compare_liners.py`, and `speed_vs_wear.py`. The interface uses the same calculations:

- Numeric sorting by maximum calculated tubing wear, ascending or descending.
- Equal-weight arithmetic means of wear and pump speed.
- Grouping by the exact reported tubing-liner description.
- Mean difference: unlined mean minus HDPE mean.
- Relative difference: mean difference divided by the unlined mean, multiplied by 100. A zero reference mean produces an unavailable result, not zero.
- Scatter plots of reported pump speed versus reported maximum tubing wear.

No new wear equation, prediction model, failure-time estimate, optimization model, or safety classification is introduced. Values come from PC-PUMP design reports. PIPESIM 2023 is supplementary; there is no live connection, dependency, or simulated PIPESIM output in this application. The supplied CSV has no verified field-membership column, so field assignments are not inferred from well names. See `ENGINEERING_NOTES.md` for units and limitations.

## Data sources

The repository contains only synthetic example data (`data/demo.csv`) and a header-only CSV template. Synthetic results are explicitly labelled and are not research evidence. Original PDF reports and actual well data are excluded from GitHub.

To use actual data, choose **Upload CSV**, or place an authorized local copy at `data/wells_private.csv`. This file is excluded by `.gitignore`. Uploads are processed in memory; they do not overwrite the input files. While running locally, the browser sends uploaded data to the local Python server. On any future hosted deployment, uploads would instead go to that deployment's server.

Required CSV columns:

| Column | Unit or accepted value |
|---|---|
| `well_name` | Unique well identifier, at most 100 characters |
| `wear_rate` | Maximum calculated tubing wear, %/year; 15 means 15%/year |
| `pump_speed_rpm` | Pump speed in RPM |
| `tubing_liner_source` | `HDPE Liner` or `No Liner/Coating` |

Use comma-separated UTF-8 data. Files are limited to 5 MB and 10,000 wells. Missing required values, duplicate identifiers, unknown liners, negative numbers, NaN, and infinity are rejected. Valid zero values are retained. Optional source fields appear in the well-record view and exported report.

## Workspace

1. Select the local dataset, synthetic example, or upload a CSV.
2. Filter by liner, speed range, and well name. Metrics and group comparisons use the selected wells.
3. Choose highest or lowest wear and the number of wells to display. The optional mean reference uses the full dataset and states its size.
4. Inspect group counts, wear means, speed means, and relative differences.
5. Inspect individual wells and source PDF page references.
6. Download charts as 300-dpi PNG files or data as CSV. Download the self-contained English HTML report from the top toolbar; open it in a browser and print or save as PDF.

The report records generation time in UTC, source type, active filters, sample sizes, descriptive results, limitations, and per-well source references. Browser print layout may vary. Reports and PNG files are generated from the current data, never illustrative engineering results.

## Code structure

| File | Responsibility |
|---|---|
| `analysis.py` | CSV validation, grouping, summaries, ranking, and safe CSV export |
| `app.py` | English Streamlit interface and Matplotlib figures |
| `reporting.py` | Self-contained printable HTML reports using the same analysis functions |
| `tests/` | Calculation, validation, report, and interface tests |
| `.streamlit/config.toml` | Restrained theme and upload size limit |

## Validation

```bash
python -m unittest discover -s tests -v
```

The interface tests use synthetic data, including when private data is present. Local regression checks additionally compare the source data to the student's earlier output. No actual well records are included in repository tests.

## Academic documentation

Retain original source reports, extraction records, final code, interface screenshots, and exported figures. Explain the Python calculations and source limitations during the presentation. This interface was developed with AI assistance from the student's existing exercises; follow the institution's disclosure requirements.
