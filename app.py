
import io, re
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Optional: local lightweight "AI" search
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _AI_OK = True
except Exception:
    _AI_OK = False

# ---- App Config ----
st.set_page_config(
    page_title="نظام إدارة الأصول - النسخة الاحترافية",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Style (CSS only; emojis for icons) ----
st.markdown('''
<style>
:root {
  --brand: #1f77b4;
}
/* Arabic-friendly fonts if available on system */
html, body, [class*="css"]  {
  font-family: "Tajawal", "Cairo", "Segoe UI", "Helvetica", "Arial", sans-serif;
}
.header {
  font-size: 2.2rem; color: var(--brand); text-align:center;
  margin: 0 0 1rem 0; padding: .75rem 0; border-bottom: 3px solid var(--brand);
}
.kpis {display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 1rem 0;}
.card {
  background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,.08);
  border-left: 5px solid var(--brand);
}
.card h3 {margin:0 0 .35rem 0; color: var(--brand); font-size: 1rem;}
.card .big {font-weight: 700; font-size: 1.35rem; color: #222;}
.card small {color:#666}
.section-title {
  background: linear-gradient(135deg, #eceff1, #ffffff);
  border-radius: 10px; padding: 10px 14px; margin: 14px 0;
  border: 1px solid #e0e0e0; font-weight: 700;
}
.badge {
  display:inline-block; padding: 2px 8px; border:1px solid #e0e0e0; border-radius: 999px; font-size:.8rem; color:#444;
  background:#fafafa; margin-left: 6px;
}
.footer {
  text-align:center; padding: 12px; border-radius: 10px; color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2); margin-top: 14px;
}
</style>
''', unsafe_allow_html=True)

st.markdown('<div class="header">🚀 نظام إدارة الأصول — النسخة الاحترافية</div>', unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.header("📁 تحميل البيانات")
    uploaded = st.file_uploader("ارفع ملف Excel", type=["xlsx", "xls"])
    st.caption("سيتم استخدام الهيدر من الصف الثاني تلقائياً (header=1).")
    st.markdown("---")
    st.header("⚙️ الإعدادات")
    show_ai = st.toggle("تفعيل مساعد الأسئلة (محلي)", value=True if _AI_OK else False, help="يتطلب scikit-learn")
    st.caption("الإصدار: 7.0 — تصميم احترافي + تبويبات + تصدير + ذكاء محلي")

if uploaded is None:
    st.info("👆 ارفع ملف السجل (Excel) للبدء.")
    st.stop()

# ---- Data Loading & Prep ----
@st.cache_data(show_spinner=True)
def load_data(uploaded_file):
    df_raw = pd.read_excel(uploaded_file, header=1)
    df = df_raw.loc[:, [c for c in df_raw.columns if str(c).strip() and not str(c).startswith("Unnamed")]].copy()
    # Attempt type conversions for common financial fields (based on typical names)
    for cand in ["Cost","Net Book Value","Accumulated Depreciation","Residual Value","القيمة الدفترية","التكلفة","الاستهلاك المتراكم","القيمة المتبقية"]:
        if cand in df.columns:
            df[cand] = pd.to_numeric(df[cand], errors="coerce")
    return df

df = load_data(uploaded)

# Column Map (best-effort Arabic/English)
ALIASES = {
    "asset_id": ["رقم الأصل الفريد","رقم الأصل الفريد بالجهة","Unique Asset Number","Unique Asset Number in the entity","الرقم التسلسلي"],
    "tag": ["Tag number","رقم البطاقة","الوسم","باركود","barcode","tag"],
    "desc": ["وصف الأصل","Asset Description","الوصف","Asset Description For Maintenance Purpose"],
    "cost": ["التكلفة","Cost"],
    "nbv": ["Net Book Value","القيمة الدفترية"],
    "acc_dep": ["الاستهلاك المتراكم","Accumulated Depreciation"],
    "residual": ["Residual Value","القيمة المتبقية"],
    "city": ["المدينة","City"],
    "region": ["المنطقة","Region"],
    "country": ["الدولة","Country"],
    "coords": ["الإحداثيات","إحداثيات","Geographical Coordinates"],
    "building": ["رقم المبنى","Building Number","Building"],
    "floor": ["رقم الدور","Floors Number","Floor"],
    "room": ["رقم الغرفة/المكتب","Room/office Number","Room"],
    "manufacturer": ["المصنع","Manufacturer"],
}

def pick_col(df, key):
    for alias in ALIASES.get(key, []):
        for c in df.columns:
            if str(c).strip().lower() == str(alias).strip().lower():
                return c
        # contains match
        for c in df.columns:
            if str(alias).strip().lower() in str(c).strip().lower():
                return c
    return None

COLS = {k: pick_col(df, k) for k in ALIASES.keys()}

# ---- Tabs ----
tab_dash, tab_search, tab_detail, tab_analytics, tab_ai = st.tabs(["📊 لوحة التحكم", "🔎 البحث", "🧾 بطاقة أصل", "📈 تحليلات", "🤖 مساعد الأسئلة"])

# ---- Dashboard ----
with tab_dash:
    st.markdown('<div class="section-title">📌 لمحة عامة</div>', unsafe_allow_html=True)
    total_assets = len(df)
    total_cost = df[COLS["cost"]].sum() if COLS["cost"] and COLS["cost"] in df.columns else 0
    total_nbv = df[COLS["nbv"]].sum() if COLS["nbv"] and COLS["nbv"] in df.columns else 0
    avg_cost = (total_cost / total_assets) if total_assets else 0
    dep_total = (df[COLS["cost"]] - df[COLS["nbv"]]).sum() if COLS["cost"] and COLS["nbv"] in df.columns and COLS["nbv"] else 0
    dep_rate = (dep_total / total_cost * 100) if total_cost else 0

    # KPIs
    kpi_html = f'''
    <div class="kpis">
      <div class="card"><h3>📦 إجمالي الأصول</h3><div class="big">{total_assets:,}</div><small>الأصول المسجلة</small></div>
      <div class="card"><h3>💰 إجمالي التكلفة</h3><div class="big">{total_cost:,.0f} ريال</div><small>قيمة الشراء</small></div>
      <div class="card"><h3>📘 القيمة الدفترية</h3><div class="big">{total_nbv:,.0f} ريال</div><small>صافي القيمة</small></div>
      <div class="card"><h3>📉 متوسط التكلفة</h3><div class="big">{avg_cost:,.0f} ريال</div><small>للأصل الواحد</small></div>
    </div>
    '''
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.caption(f"معدل الاستهلاك التقديري: {dep_rate:.1f}%")

    st.markdown('<div class="section-title">📍 توزيع حسب المدينة <span class="badge">Top 10</span></div>', unsafe_allow_html=True)
    if COLS["city"] and COLS["city"] in df.columns:
        city_counts = df[COLS["city"]].value_counts().head(10)
        if len(city_counts):
            fig = plt.figure(figsize=(8, 4))
            plt.bar(city_counts.index.astype(str), city_counts.values)
            plt.xticks(rotation=30, ha="right")
            plt.title("توزيع الأصول حسب المدينة")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("لا توجد بيانات كافية لعرض المدن.")
    else:
        st.warning("لم يتم التعرف على عمود المدينة تلقائياً.")

# ---- Search ----
with tab_search:
    st.markdown('<div class="section-title">🔍 البحث الذكي</div>', unsafe_allow_html=True)
    q = st.text_input("اكتب نص البحث (رقم أصل، وسم، وصف، موقع...):", key="q_search")
    df_view = df.copy()
    # quick smart search across object columns
    if q.strip():
        mask = np.zeros(len(df_view), dtype=bool)
        obj_cols = df_view.select_dtypes(include=["object"]).columns
        ql = q.strip().lower()
        for c in obj_cols:
            col_match = df_view[c].astype(str).str.lower().str.contains(ql, na=False)
            mask = mask | col_match.values
        df_view = df_view[mask]
    st.caption(f"عدد النتائج: {len(df_view):,}")
    st.dataframe(df_view.head(300), use_container_width=True)

    # Export filtered
    exp_buf = io.BytesIO()
    df_view.to_excel(exp_buf, index=False)
    exp_buf.seek(0)
    st.download_button("⬇️ تحميل النتائج (Excel)", exp_buf, "search_results.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---- Detail + PDF ----
with tab_detail:
    st.markdown('<div class="section-title">🧾 بطاقة أصل قابلة للطباعة</div>', unsafe_allow_html=True)
    # choose id column
    id_col = COLS["asset_id"] or st.selectbox("اختر عمود رقم الأصل:", options=df.columns)
    ids = df[id_col].dropna().astype(str).unique().tolist() if id_col in df.columns else []
    pick = st.selectbox("اختر رقم الأصل:", [""] + ids)
    if pick:
        recs = df[df[id_col].astype(str) == str(pick)].head(1).to_dict(orient="records")
        if recs:
            rec = recs[0]
            # Two-column pretty view
            l, r = st.columns(2)
            with l:
                st.markdown("**بيانات التعريف**")
                for key in ["asset_id","tag","desc","manufacturer"]:
                    coln = COLS.get(key)
                    if coln and coln in df.columns:
                        st.write(f"**{coln}**: {rec.get(coln, '—')}")
            with r:
                st.markdown("**القيم المالية**")
                for key in ["cost","nbv","acc_dep","residual"]:
                    coln = COLS.get(key)
                    if coln and coln in df.columns:
                        st.write(f"**{coln}**: {rec.get(coln, '—')}")

                st.markdown("**الموقع**")
                for key in ["country","region","city","building","floor","room","coords"]:
                    coln = COLS.get(key)
                    if coln and coln in df.columns:
                        st.write(f"**{coln}**: {rec.get(coln, '—')}")

                # mini map if coordinates look like 'lat,lon'
                coords_col = COLS.get("coords")
                def _parse_coords(val):
                    s = str(val or "").replace("،", ",")
                    if "," in s:
                        try:
                            lat, lon = [float(x.strip()) for x in s.split(",", 1)]
                            if abs(lat) <= 90 and abs(lon) <= 180: return lat, lon
                        except Exception:
                            return None
                    return None
                if coords_col and coords_col in df.columns and rec.get(coords_col):
                    got = _parse_coords(rec.get(coords_col))
                    if got:
                        lat, lon = got
                        fig = plt.figure(figsize=(3.5, 3))
                        ax = plt.gca()
                        ax.scatter([lon], [lat], s=50)
                        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_title("موقع تقريبي")
                        ax.set_xlim(lon-0.02, lon+0.02); ax.set_ylim(lat-0.02, lat+0.02)
                        st.pyplot(fig)

            st.markdown("---")
            if st.button("🖨️ تحميل بطاقة الأصل (PDF)"):
                try:
                    # simple PDF using fpdf
                    from fpdf import FPDF
                    pdf = FPDF(orientation="P", unit="mm", format="A4")
                    pdf.add_page()
                    pdf.set_font("Arial","B",14)
                    pdf.cell(0, 10, "Asset Sheet", 0, 1, "C")
                    pdf.set_font("Arial","",11)
                    for k, v in rec.items():
                        pdf.cell(0, 8, f"{k}: {v}", 0, 1, "L")
                    out = pdf.output(dest="S").encode("latin1", "ignore")
                    st.download_button("تحميل PDF", data=out, file_name=f"asset_{pick}.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"تعذر توليد PDF: {e}")

# ---- Analytics ----
with tab_analytics:
    st.markdown('<div class="section-title">📈 تحليلات سريعة</div>', unsafe_allow_html=True)

    # Financial distributions
    c1, c2 = st.columns(2)
    if COLS["cost"] and COLS["cost"] in df.columns:
        with c1:
            vals = df[COLS["cost"]].dropna()
            if len(vals):
                fig = plt.figure(figsize=(7,4))
                plt.hist(vals, bins=20)
                plt.title("توزيع التكلفة")
                plt.xlabel("Cost"); plt.ylabel("Count")
                plt.tight_layout()
                st.pyplot(fig)
    if COLS["nbv"] and COLS["nbv"] in df.columns:
        with c2:
            vals = df[COLS["nbv"]].dropna()
            if len(vals):
                fig = plt.figure(figsize=(7,4))
                plt.hist(vals, bins=20)
                plt.title("توزيع القيمة الدفترية")
                plt.xlabel("NBV"); plt.ylabel("Count")
                plt.tight_layout()
                st.pyplot(fig)

    # Depreciation rate scatter if possible
    if COLS["cost"] and COLS["nbv"] and COLS["cost"] in df.columns and COLS["nbv"] in df.columns:
        good = df.dropna(subset=[COLS["cost"], COLS["nbv"]]).copy()
        good = good[good[COLS["cost"]] > 0]
        if len(good):
            good["dep_rate"] = (good[COLS["cost"]] - good[COLS["nbv"]]) / good[COLS["cost"]] * 100
            fig = plt.figure(figsize=(7,4))
            plt.scatter(good[COLS["cost"]], good["dep_rate"], alpha=.6)
            plt.title("العلاقة بين التكلفة ومعدل الاستهلاك")
            plt.xlabel("Cost"); plt.ylabel("Depreciation Rate %")
            plt.tight_layout()
            st.pyplot(fig)

# ---- AI-like Q&A ----
with tab_ai:
    st.markdown('<div class="section-title">🤖 مساعد الأسئلة (محلي)</div>', unsafe_allow_html=True)
    if not _AI_OK and show_ai:
        st.warning("لم يتم العثور على scikit-learn. عطّل الخيار أو ثبّت المكتبة.")
    if show_ai and _AI_OK:
        # Build index
        @st.cache_resource(show_spinner=False)
        def _build_index(df):
            def row_to_text(r):
                parts = []
                for c in df.columns:
                    v = r.get(c)
                    if pd.notna(v) and str(v).strip():
                        parts.append(f"{c}: {v}")
                return " | ".join(parts)
            texts = df.apply(row_to_text, axis=1).fillna("")
            vect = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=2)
            try:
                X = vect.fit_transform(texts)
            except ValueError:
                vect = TfidfVectorizer(analyzer="char", ngram_range=(3,5), min_df=1)
                X = vect.fit_transform(texts)
            return vect, X

        vect, X = _build_index(df)
        q_text = st.text_input("اكتب سؤالك (مثال: كم القيمة الدفترية لأصل 12345؟)")
        k = st.slider("عدد السجلات المرجعية", 1, 20, 5)
        if q_text.strip():
            q_vec = vect.transform([q_text])
            sims = cosine_similarity(q_vec, X)[0]
            idx = sims.argsort()[::-1][:k]
            cand = df.iloc[idx].copy()
            cand["_score"] = sims[idx]
            st.write("**أقرب سجلات:**")
            st.dataframe(cand.drop(columns=["_score"]), use_container_width=True)
            # Try to detect a field to answer directly
            intents = [
                ("nbv", ["القيمة الدفترية","nbv"]),
                ("cost", ["التكلفة","cost"]),
                ("acc_dep", ["الاستهلاك المتراكم"]),
                ("residual", ["القيمة المتبقية","residual"]),
                ("city", ["المدينة","city","موقع"]),
            ]
            which = None
            ql = q_text.lower()
            for key, kws in intents:
                for kw in kws:
                    if kw in ql: which = key; break
                if which: break
            if which and COLS.get(which) and COLS[which] in cand.columns:
                st.markdown("**إجابة مباشرة (حقل محدد):**")
                lines = []
                idname = COLS.get("asset_id") or COLS.get("tag") or cand.columns[0]
                for _, r in cand.head(5).iterrows():
                    ident = r.get(idname, "—")
                    val = r.get(COLS[which], "—")
                    lines.append(f"- الأصل **{ident}**: {val}")
                st.write("\n".join(lines))
            else:
                st.info("لم أحدد حقلاً واضحاً، أعرض لك أقرب سجلات مطابقة.")
    else:
        st.info("يمكن تفعيل المساعد من الشريط الجانبي.")

# ---- Footer ----
st.markdown(f'<div class="footer">✅ النسخة الاحترافية — {datetime.now():%Y-%m-%d}</div>', unsafe_allow_html=True)
