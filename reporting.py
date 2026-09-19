"""Self-contained, printable HTML report using the existing calculation engine."""
from datetime import datetime, timezone
from html import escape
from analysis import summary, groups, rank


def build_report(all_rows, selected_rows, source, speed_range, liners, search):
    stats = summary(selected_rows)
    if not stats:
        raise ValueError('A report requires at least one selected well.')
    esc = lambda v: escape(str(v), quote=True)
    def table(headers, records):
        return '<table><thead><tr>' + ''.join('<th>'+esc(h)+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in records) + '</tbody></table>'
    group_rows = []
    for liner, result in groups(selected_rows).items():
        group_rows.append([liner, result['count'] if result else 0, f"{result['mean_wear']:.2f}" if result else 'Not available', f"{result['mean_speed']:.2f}" if result else 'Not available'])
    top = rank(selected_rows)
    results = table(['Well', 'Maximum calculated wear (%/year)', 'Speed (RPM)', 'Liner'], [[r['well_name'],f"{r['wear_rate']:.2f}",f"{r['pump_speed_rpm']:.2f}",r['tubing_liner_source']] for r in top])
    source_table = table(['Well','Source PDF','Wear page','Analysis page','Completion page','PC-PUMP version','Wear notes'], [[r['well_name']]+[r.get(k) or 'Not provided' for k in ['source_file','wear_page','analysis_page','completion_page','pc_pump_version','wear_notes']] for r in selected_rows])
    title = 'PCP performance analysis report'
    synthetic = '<p><strong>SYNTHETIC EXAMPLE — not research results.</strong></p>' if source == 'Synthetic example' else ''
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title><style>
body{{font:15px/1.6 system-ui,sans-serif;color:#193447;background:#f7f7f3;max-width:1100px;margin:auto;padding:36px}}h1{{font-size:28px}}h2{{font-size:20px;margin-top:32px}}table{{border-collapse:collapse;width:100%;font-size:12px;background:white}}td,th{{border:1px solid #d5dcd9;padding:9px;text-align:left;overflow-wrap:anywhere}}th{{background:#e8eeeb}}.scroll{{overflow-x:auto}}@media print{{body{{padding:0;background:white}}thead{{display:table-header-group}}tr{{break-inside:avoid}}h2{{break-after:avoid}}}}
</style></head><body><h1>{title}</h1>
<p>Generated {esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}. Source: {esc(source)}.</p>{synthetic}
<p>Field context: Marmul, Nimr and Rima, Oman. The supplied dataset has no verified field-membership column; no field assignment is inferred.</p>
<h2>Selection and results</h2><p>{len(selected_rows)} of {len(all_rows)} wells. Speed range: {speed_range[0]:g}–{speed_range[1]:g} RPM. Liners: {esc(', '.join(liners))}. Well-name search: {esc(search.strip() or 'None')}.</p>
<p>Mean calculated wear: <strong>{stats['mean_wear']:.2f} %/year</strong>. Mean speed: {stats['mean_speed']:.2f} RPM. Calculated zero-wear records: {stats['zero_count']}.</p>
<h2>Highest calculated wear in the selected data</h2><div class="scroll">{results}</div>
<h2>Liner comparison</h2><div class="scroll">{table(['Liner','Wells','Mean wear (%/year)','Mean speed (RPM)'],group_rows)}</div>
<h2>Method and limitations</h2><p>The existing Python engine calculates equal-weight arithmetic means and numeric wear rankings. Liner-group means are descriptive comparisons. They do not control for speed, operating conditions, software versions, or correction factors. Values are copied from design reports, not independent field wear measurements. A zero can reflect model exclusions and does not prove absence of physical wear. No failure date, safe operating threshold, new wear formula, or predictive result is calculated.</p>
<p>Percentages retain report units: 15 means 15%/year. Correction factors mentioned in source notes are not reapplied. The report uses selected wells; the optional reference line in the application's ranking chart uses the full input dataset.</p>
<p>PIPESIM 2023 is a supplementary simulation tool. This report contains no PIPESIM outputs and requires no live connection.</p>
<h2>Source traceability for selected wells</h2><div class="scroll">{source_table}</div>
</body></html>'''
    return html.encode('utf-8')
