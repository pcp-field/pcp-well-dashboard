"""PCP dashboard: run with `streamlit run app.py`."""
from pathlib import Path
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from analysis import load_rows, summary, rank, groups, csv_bytes, LINERS

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='PCP | Well Explorer', page_icon='◉', layout='wide')
st.markdown('''<style>
.stApp {background:#f7f8fa;}
.block-container {padding-top:4rem;max-width:1400px;}
h1,h2,h3 {color:#132f43;}
[data-testid="stMetric"] {background:white;border:1px solid #e0e7ec;border-radius:12px;padding:18px;}
[data-testid="stMetricValue"] {color:#007f80;}
[data-testid="stSidebar"] {background:#edf3f5;}
[data-testid="stCaptionContainer"] {color:#526775;}
</style>''', unsafe_allow_html=True)

st.caption('MECHANICAL PERFORMANCE  /  PROGRESSIVE CAVITY PUMPS')
st.title('PCP Well Explorer')
st.markdown('**تحليل أداء الآبار** — ترتيب التآكل، مقارنة البطانة، واستكشاف ظروف التشغيل.')

with st.sidebar:
    st.header('مصدر البيانات')
    local = ROOT / 'data' / 'wells_private.csv'
    options = ['بيانات المشروع المحلية', 'بيانات تجريبية', 'رفع ملف CSV'] if local.exists() else ['بيانات تجريبية', 'رفع ملف CSV']
    source = st.radio('اختر البيانات', options, key='source')
    uploaded = st.file_uploader('ملف بيانات الآبار', type=['csv'], key='upload') if source == 'رفع ملف CSV' else None
    st.download_button('تنزيل قالب CSV', (ROOT / 'data/template.csv').read_bytes(), 'template.csv', 'text/csv')
    st.caption('الملف التجريبي للتجربة فقط. بيانات المشروع المحلية مستبعدة من GitHub.')

if source == 'رفع ملف CSV' and uploaded is None:
    st.info('ارفع ملف CSV للبدء. القالب في القائمة الجانبية يوضح الأعمدة المطلوبة.')
    st.stop()
try:
    if source == 'رفع ملف CSV':
        raw = uploaded.getvalue()
    else:
        raw = (local if source == 'بيانات المشروع المحلية' else ROOT / 'data/demo.csv').read_bytes()
    rows = load_rows(raw)
except (ValueError, OSError) as e:
    st.error(str(e))
    st.stop()

if source == 'بيانات تجريبية':
    st.warning('بيانات اصطناعية للتجربة — ليست آبار الدراسة ولا تصلح للاستشهاد بها كنتائج بحث.')
else:
    st.info('النتائج وصفية لمخرجات تقارير التصميم؛ لا تمثل قياسات تآكل ميدانية أو تنبؤًا بموعد الفشل.')

with st.sidebar:
    st.divider()
    st.header('تصفية الآبار')
    liner_filter = st.multiselect('نوع البطانة', LINERS, default=LINERS, key='liner_filter')
    speed_low = min(r['pump_speed_rpm'] for r in rows)
    speed_high = max(r['pump_speed_rpm'] for r in rows)
    speed_range = st.slider('السرعة RPM', speed_low, speed_high, (speed_low, speed_high), key='speed') if speed_low < speed_high else (speed_low, speed_high)
    if speed_low == speed_high:
        st.caption(f'سرعة جميع الآبار: {speed_low:g} RPM')
    search = st.text_input('ابحث باسم البئر', key='search')
    st.caption('المؤشرات والمقارنات تتحدث حسب التصفية. متوسط الملف الكامل يظهر منفصلًا على رسم الترتيب.')

filtered = [r for r in rows if r['tubing_liner_source'] in liner_filter and speed_range[0] <= r['pump_speed_rpm'] <= speed_range[1] and search.strip().casefold() in r['well_name'].casefold()]
if not filtered:
    st.warning('لا توجد آبار تطابق التصفية. عدّل الاختيارات في القائمة الجانبية.')
    st.stop()
all_stats, stats = summary(rows), summary(filtered)
st.caption(f"الآبار المعروضة: {len(filtered)} من {len(rows)} | الوحدات: التآكل %/سنة، السرعة RPM")
cols = st.columns(4)
for col, label, value in zip(cols, ['عدد الآبار المعروضة', 'متوسط التآكل %/سنة', 'متوسط السرعة RPM', 'نتائج تآكل بصفر'], [stats['count'], f"{stats['mean_wear']:.2f}", f"{stats['mean_speed']:.2f}", stats['zero_count']]):
    col.metric(label, value)

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.labelcolor': '#334b5a', 'text.color': '#193447', 'figure.facecolor': 'white'})
COLORS = {'HDPE Liner': '#008b89', 'No Liner/Coating': '#477ea6'}

def chart(fig, filename):
    """Display a figure and supply an independent 300-dpi PNG download."""
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    st.pyplot(fig, width='stretch')
    st.download_button('تنزيل الرسم PNG', buffer.getvalue(), filename, 'image/png', key=filename)
    plt.close(fig)

ranking, comparison, relation, details = st.tabs(['ترتيب الآبار', 'مقارنة البطانة', 'السرعة والتآكل', 'بيانات ومصادر'])
with ranking:
    st.subheader('الآبار حسب معدل التآكل المحسوب')
    left, right = st.columns([1, 2])
    with left:
        order = st.radio('الترتيب', ['الأعلى أولًا', 'الأقل أولًا'], horizontal=True, key='order')
        count = st.number_input('عدد الآبار في الرسم', min_value=1, max_value=min(20, len(filtered)), value=min(5, len(filtered)), step=1, key='count')
        show_mean = st.checkbox('إظهار متوسط الملف الكامل', value=True)
        st.caption('خط المتوسط مرجع وصفي، وليس حدًا للسلامة. تعادل القيم يُرتّب حسب اسم البئر.')
    selected = rank(filtered, int(count), order == 'الأعلى أولًا')
    with right:
        fig, ax = plt.subplots(figsize=(9, max(3.5, len(selected) * .37)))
        bars = ax.barh([r['well_name'] for r in selected], [r['wear_rate'] for r in selected], color='#008b89')
        ax.invert_yaxis()
        ax.bar_label(bars, fmt='%.2f', padding=5)
        if show_mean:
            ax.axvline(all_stats['mean_wear'], color='#bb6940', linestyle='--', label=f"Full dataset mean: {all_stats['mean_wear']:.2f} (n={len(rows)})")
            ax.legend(loc='lower right', fontsize=8)
        maximum = max([r['wear_rate'] for r in selected] + ([all_stats['mean_wear']] if show_mean else []))
        ax.set_xlim(0, max(1, maximum) * 1.2)
        ax.set_xlabel('Maximum calculated tubing wear (%/year)')
        ax.set_title(('Highest' if order == 'الأعلى أولًا' else 'Lowest') + f' {len(selected)} wells in selected data')
        chart(fig, 'ranked_wells.png')
    st.dataframe(pd.DataFrame(selected)[['well_name', 'wear_rate', 'pump_speed_rpm', 'tubing_liner_source']], hide_index=True, width='stretch')
    st.download_button('تنزيل الآبار المرتبة CSV', csv_bytes(selected), 'ranked_wells.csv', 'text/csv')

with comparison:
    st.subheader('مقارنة المجموعتين في البيانات المعروضة')
    group_stats = groups(filtered)
    present = {k: v for k, v in group_stats.items() if v}
    table = [{'Liner': k, 'Wells': v['count'], 'Mean wear (%/year)': round(v['mean_wear'], 2), 'Mean speed (RPM)': round(v['mean_speed'], 2)} for k, v in present.items()]
    st.dataframe(pd.DataFrame(table), hide_index=True, width='stretch')
    if len(present) < 2:
        st.info('تحتاج المقارنة إلى آبار من كلا النوعين. عدّل التصفية أو البيانات.')
    else:
        hdpe, unlined = group_stats[LINERS[0]], group_stats[LINERS[1]]
        difference = unlined['mean_wear'] - hdpe['mean_wear']
        st.metric('فرق المتوسطين: بدون بطانة ناقص HDPE (%/سنة)', f'{difference:.2f}')
        if unlined['mean_wear'] != 0:
            pct = difference / unlined['mean_wear'] * 100
            st.caption(f'الفرق النسبي باستخدام مجموعة بدون بطانة كمرجع: {pct:.2f}%. الموجب يعني متوسط HDPE أقل، والسالب يعني أنه أعلى.')
        else:
            st.caption('الفرق النسبي غير معرّف لأن متوسط المجموعة المرجعية صفر.')
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
    st.caption('مقارنة وصفية لا تعزل تأثير البطانة عن السرعة أو ظروف التشغيل أو اختلاف إعدادات التصميم. المتوسطات ليست ضمانًا لنسبة تحسن عند تغيير البطانة.')

with relation:
    st.subheader('كل نقطة تمثل بئرًا')
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
    st.caption('قد تتداخل نقاط متطابقة. الرسم يوضح العلاقات ولا يثبت أن عاملًا واحدًا سبب الاختلاف. لا تُستنتج نتائج خارج نطاق السرعات الموجود.')

with details:
    st.subheader('بيانات البئر ومصدر القيم')
    chosen = st.selectbox('اختر بئرًا', [r['well_name'] for r in filtered], key='well')
    well = next(r for r in filtered if r['well_name'] == chosen)
    st.dataframe(pd.DataFrame([{'Field': k, 'Value': str(v)} for k, v in well.items()]), hide_index=True, width='stretch')
    st.download_button('تنزيل البيانات المعروضة CSV', csv_bytes(filtered), 'filtered_wells.csv', 'text/csv')
    with st.expander('طريقة التحليل وحدود النتائج', expanded=True):
        st.markdown('''- المتوسط هو مجموع القيم مقسومًا على عدد الآبار، بأوزان متساوية.
- القيم المئوية مخزنة كما تظهر في التقرير: 15 تعني 15%/سنة، ولا تُضرب في 100.
- التآكل الصفري في بعض تقارير PC-PUMP لا يثبت غياب التآكل الفعلي؛ بعض المكونات لا يُحسب تآكلها الداخلي.
- عند توفر حقول المصدر، راجع إصدار البرنامج وملاحظات معاملات التصحيح قبل المقارنة. تُعرض نتائج التقرير كما هي دون إعادة تطبيق المعامل.
- هذه الأداة للتحليل الوصفي؛ لا تحسب وقت الفشل أو حدود تشغيل آمنة.
- التحليلات تعمل على البيانات بعد التصفية، باستثناء خط متوسط الملف الكامل في رسم الترتيب.''')

st.divider()
st.caption('PCP Well Explorer · Python + Streamlit · ملف البيانات الأصلي لا يُعدّل أثناء التحليل.')
