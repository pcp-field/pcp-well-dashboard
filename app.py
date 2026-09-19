"""PCP dashboard: run with `streamlit run app.py`."""
from pathlib import Path
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from analysis import load_rows, summary, rank, groups, csv_bytes, LINERS
from reporting import build_report

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='PCP | Well Explorer', page_icon='◉', layout='wide')
st.markdown('''<style>
.stApp {background:#f7f7f3;}
.block-container {padding-top:3rem;max-width:1440px;}
h1,h2,h3 {color:#132f43;}
h1 {font-size:2rem !important;padding-bottom:.35rem !important;}
h2,h3 {font-size:1.25rem !important;}
[data-testid="stMetric"] {background:white;border:1px solid #e0e7ec;border-radius:6px;padding:14px;}
[data-testid="stMetricValue"] {color:#487c79;font-size:1.8rem;}
[data-testid="stSidebar"] {background:#efefea;}
[data-testid="stCaptionContainer"] {color:#526775;}
@media (max-width: 760px) {
.block-container {padding:4rem 1rem 1rem;}
h1 {font-size:1.65rem !important;}
[data-testid="stMetric"] {padding:12px;}
[data-baseweb="tab-list"] {overflow-x:auto;}
}
</style>''', unsafe_allow_html=True)

st.caption('OMAN  /  MECHANICAL ENGINEERING  /  FINAL-YEAR PROJECT')
st.title('PCP performance workspace')
st.caption('Field context: Marmul · Nimr · Rima.')

with st.sidebar:
    st.header('Dataset')
    local = ROOT / 'data' / 'wells_private.csv'
    options = ['Local project data', 'Synthetic example', 'Upload CSV'] if local.exists() else ['Synthetic example', 'Upload CSV']
    source = st.radio('Data source', options, key='source')
    uploaded = st.file_uploader('Well dataset (CSV)', type=['csv'], key='upload') if source == 'Upload CSV' else None
    st.download_button('Download CSV template', (ROOT / 'data/template.csv').read_bytes(), 'template.csv', 'text/csv')
    st.caption('Synthetic data is for demonstration only. Local project data is excluded from GitHub.')

if source == 'Upload CSV' and uploaded is None:
    st.info('Upload a CSV to begin. The sidebar template lists the required columns.')
    st.stop()
try:
    if source == 'Upload CSV':
        raw = uploaded.getvalue()
    else:
        raw = (local if source == 'Local project data' else ROOT / 'data/demo.csv').read_bytes()
    with st.spinner('Validating and loading well data…'):
        rows = load_rows(raw)
except (ValueError, OSError) as e:
    st.error('Dataset could not be loaded. ' + str(e))
    st.caption('Correct the file and upload it again. Required columns are listed in the CSV template.')
    st.stop()

if source == 'Synthetic example':
    st.warning('SYNTHETIC EXAMPLE — These are not study wells. Do not use these results as research evidence.')

with st.sidebar:
    st.divider()
    st.header('Filters')
    liner_filter = st.multiselect('Tubing liner', LINERS, default=LINERS, key='liner_filter')
    speed_low = min(r['pump_speed_rpm'] for r in rows)
    speed_high = max(r['pump_speed_rpm'] for r in rows)
    speed_range = st.slider('Pump speed (RPM)', speed_low, speed_high, (speed_low, speed_high), key='speed') if speed_low < speed_high else (speed_low, speed_high)
    if speed_low == speed_high:
        st.caption(f'All wells operate at: {speed_low:g} RPM')
    search = st.text_input('Search well name', key='search')
    st.caption('Metrics and comparisons use filtered wells. The ranking reference line uses the full dataset.')

filtered = [r for r in rows if r['tubing_liner_source'] in liner_filter and speed_range[0] <= r['pump_speed_rpm'] <= speed_range[1] and search.strip().casefold() in r['well_name'].casefold()]
if not filtered:
    st.warning('No matching wells. Adjust the liner, speed, or well-name filters.')
    st.stop()
all_stats, stats = summary(rows), summary(filtered)
bar_left, bar_right = st.columns([3, 2])
with bar_left:
    st.success('Dataset validated', icon=None)
with bar_right:
    st.download_button('Export analysis report · HTML', build_report(rows, filtered, source, speed_range, liner_filter, search), 'pcp_analysis_report.html', 'text/html')

st.caption(f"Selected wells: {len(filtered)} of {len(rows)} | Units: wear %/year; speed RPM")
cols = st.columns(4)
for col, label, value in zip(cols, ['Selected wells', 'Mean wear (%/year)', 'Mean speed (RPM)', 'Calculated zeros'], [stats['count'], f"{stats['mean_wear']:.2f}", f"{stats['mean_speed']:.2f}", stats['zero_count']]):
    col.metric(label, value)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.labelcolor': '#334b5a', 'text.color': '#193447', 'figure.facecolor': 'white'})
COLORS = {'HDPE Liner': '#487c79', 'No Liner/Coating': '#8b99a5'}

def chart(fig, filename):
    """Display a figure and supply an independent 300-dpi PNG download."""
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    st.pyplot(fig, width='stretch')
    st.download_button('Download chart · PNG', buffer.getvalue(), filename, 'image/png', key=filename)
    plt.close(fig)

ranking, comparison, relation, details = st.tabs(['Well ranking', 'Liner comparison', 'Speed and wear', 'Data and provenance'])
with ranking:
    st.subheader('Rank wells by calculated tubing wear')
    left, right = st.columns([1, 2])
    with left:
        order = st.radio('Order', ['Highest first', 'Lowest first'], horizontal=True, key='order')
        count = st.number_input('Wells to display', min_value=1, max_value=min(20, len(filtered)), value=min(5, len(filtered)), step=1, key='count')
        show_mean = st.checkbox('Show full-dataset mean', value=True)
        st.caption('The mean is a descriptive reference, not a safety limit. Equal values are ordered by well name.')
    selected = rank(filtered, int(count), order == 'Highest first')
    with right:
        fig, ax = plt.subplots(figsize=(9, max(3.5, len(selected) * .37)))
        bars = ax.barh([r['well_name'] for r in selected], [r['wear_rate'] for r in selected], color='#487c79')
        ax.invert_yaxis()
        ax.bar_label(bars, fmt='%.2f', padding=5)
        if show_mean:
            ax.axvline(all_stats['mean_wear'], color='#193447', linestyle='--', label=f"Full dataset mean: {all_stats['mean_wear']:.2f} (n={len(rows)})")
            ax.legend(loc='lower right', fontsize=8)
        maximum = max([r['wear_rate'] for r in selected] + ([all_stats['mean_wear']] if show_mean else []))
        ax.set_xlim(0, max(1, maximum) * 1.2)
        ax.set_xlabel('Maximum calculated tubing wear (%/year)')
        ax.set_title(('Highest' if order == 'Highest first' else 'Lowest') + f' {len(selected)} wells in selected data')
        chart(fig, 'ranked_wells.png')
    st.dataframe(pd.DataFrame(selected)[['well_name', 'wear_rate', 'pump_speed_rpm', 'tubing_liner_source']].rename(columns={'well_name': 'Well', 'wear_rate': 'Wear (%/year)', 'pump_speed_rpm': 'Speed (RPM)', 'tubing_liner_source': 'Liner'}), hide_index=True, width='stretch')
    st.download_button('Download ranked wells · CSV', csv_bytes(selected), 'ranked_wells.csv', 'text/csv')

with comparison:
    st.subheader('Compare liner groups in the selected data')
    group_stats = groups(filtered)
    present = {k: v for k, v in group_stats.items() if v}
    table = [{'Liner': k, 'Wells': v['count'], 'Mean wear (%/year)': round(v['mean_wear'], 2), 'Mean speed (RPM)': round(v['mean_speed'], 2)} for k, v in present.items()]
    st.dataframe(pd.DataFrame(table), hide_index=True, width='stretch')
    if len(present) < 2:
        st.info('Both liner groups are needed for a comparison. Adjust your filters or dataset.')
    else:
        hdpe, unlined = group_stats[LINERS[0]], group_stats[LINERS[1]]
        difference = unlined['mean_wear'] - hdpe['mean_wear']
        st.metric('Mean difference: unlined minus HDPE (%/year)', f'{difference:.2f}')
        if unlined['mean_wear'] != 0:
            pct = difference / unlined['mean_wear'] * 100
            st.caption(f'Relative difference, with the unlined group as reference: {pct:.2f}%. A positive value means the HDPE mean is lower; a negative value means it is higher.')
        else:
            st.caption('Relative difference is undefined because the reference-group mean is zero.')
    if present:
        fig, ax = plt.subplots(figsize=(8, 4))
        labels = [f"{'HDPE' if k == LINERS[0] else 'No liner/coating'}\n(n={v['count']})" for k, v in present.items()]
        values = [v['mean_wear'] for v in present.values()]
        bars = ax.bar(labels, values, color=[COLORS[k] for k in present])
        ax.bar_label(bars, fmt='%.2f', padding=4)
        ax.set_ylim(0, max(1, max(values)) * 1.25)
        ax.set_ylabel('Mean calculated tubing wear (%/year)')
        ax.set_title('Liner comparison in selected data')
        chart(fig, 'liner_comparison.png')
    st.caption('This descriptive comparison does not isolate liner effects from speed, operating conditions, or design settings. It is not a guaranteed improvement from fitting a liner.')

with relation:
    st.subheader('Inspect individual wells')
    fig, ax = plt.subplots(figsize=(9, 5))
    for liner in reversed(LINERS):
        group = [r for r in filtered if r['tubing_liner_source'] == liner]
        if group:
            ax.scatter([r['pump_speed_rpm'] for r in group], [r['wear_rate'] for r in group], marker='^' if liner == LINERS[0] else 'o', color=COLORS[liner], s=70, alpha=.75, label=f'{liner} (n={len(group)})')
    ax.set_xlabel('Pump speed (RPM)')
    ax.set_ylabel('Maximum calculated tubing wear (%/year)')
    ax.set_title('Pump speed and calculated tubing wear')
    ax.legend()
    ax.grid(alpha=.15)
    chart(fig, 'speed_vs_wear.png')
    st.caption('Identical points can overlap. The plot shows associations, not causation. Do not extrapolate beyond the observed speed range.')

with details:
    st.subheader('Well record and source references')
    st.caption('PIPESIM 2023 is supplementary. No live connection or PIPESIM results are used in these calculations.')
    chosen = st.selectbox('Select a well', [r['well_name'] for r in filtered], key='well')
    well = next(r for r in filtered if r['well_name'] == chosen)
    st.dataframe(pd.DataFrame([{'Field': k, 'Value': str(v)} for k, v in well.items()]), hide_index=True, width='stretch')
    st.download_button('Download selected data · CSV', csv_bytes(filtered), 'filtered_wells.csv', 'text/csv')
    with st.expander('Method and limitations', expanded=True):
        st.markdown('''- The mean is the sum divided by the well count, with equal weight per well.
- Percentage values match the reports: 15 means 15%/year, not 0.15.
- A calculated zero does not establish absence of physical wear. Some component-internal wear is excluded by the source model.
- Review source software versions and wear-factor notes before comparisons. Reported values are preserved without reapplying correction factors.
- This tool does not estimate failure dates or safe operating limits.
- Analyses use filtered data, except the full-dataset mean reference in the ranking chart.''')

st.divider()
st.caption('PCP Well Explorer · Python + Streamlit · Source data is not modified during analysis.')
