
import io
import pandas as pd
import streamlit as st
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns

st.set_page_config(page_title="إدارة وعرض سجلات الأصول - PoC", layout="wide")

st.title("نموذج أولي: عرض سجل الأصول وتوليد ورقة تفصيلية قابلة للطباعة")

with st.sidebar:
    st.header("تحميل ملف السجل")
    uploaded = st.file_uploader("ارفع ملف Excel للسجل", type=["xlsx","xls"])
    st.markdown("---")
    st.caption("ملاحظة: سيُحاول النظام قراءة الهيدر من الصف الثاني تلقائيًا (header=1).")

if uploaded is None:
    st.info("الرجاء رفع ملف السجل (Excel).")
    st.stop()

# Read data
try:
    df_raw = pd.read_excel(uploaded, header=1)  # header row = 1 (zero-based)
except Exception as e:
    st.error(f"تعذر قراءة الملف: {e}")
    st.stop()

# Clean/prepare
df = prepare_dataframe(df_raw)

# Column guessing (based on common Arabic headers)
colmap = guess_columns(df.columns)

with st.expander("تعيين/تأكيد أسماء الأعمدة (يمكن تعديلها إذا لزم):", expanded=False):
    for k, v in colmap.items():
        colmap[k] = st.selectbox(f"{k}", options=["(غير موجود)"] + list(df.columns), index=(list(df.columns).index(v)+1) if v in df.columns else 0)

# Filters/Search
st.subheader("البحث والتصفية")
search = st.text_input("ابحث برقم الأصل/الوسم/الوصف:", "")
city_col = colmap.get("City")
cities = sorted([c for c in df[city_col].dropna().unique().tolist()]) if city_col and city_col in df.columns else []
col1, col2, col3 = st.columns([2,1,1])
with col1:
    pass
with col2:
    city = st.selectbox("المدينة", ["الكل"] + cities) if cities else "الكل"
with col3:
    st.write("")

# Apply search
df_view = df.copy()

def match_row(row):
    s = str(search).strip()
    if not s:
        return True
    concat = " ".join([str(row.get(colmap.get("Asset Unique No"), "")),
                       str(row.get(colmap.get("Tag Number"), "")),
                       str(row.get(colmap.get("Description"), ""))]).lower()
    return s.lower() in concat

if search:
    df_view = df_view[df_view.apply(match_row, axis=1)]

if city != "الكل" and city_col and city_col in df_view.columns:
    df_view = df_view[df_view[city_col] == city]

st.caption(f"عدد السجلات المطابقة: {len(df_view):,}")
st.dataframe(df_view.head(200))

st.markdown("---")
st.subheader("تفاصيل أصل محدد")
id_col = colmap.get("Asset Unique No")
if not id_col or id_col not in df.columns:
    st.warning("لم يتم تعيين عمود 'رقم الأصل الفريد بالجهة'. حدده من أعلى.")
    st.stop()

asset_ids = df_view[id_col].dropna().astype(str).unique().tolist()
selected_id = st.selectbox("اختر رقم الأصل", [""] + asset_ids)

if not selected_id:
    st.stop()

row = df[df[id_col].astype(str) == str(selected_id)].head(1)
if row.empty:
    st.warning("لم يتم العثور على هذا الأصل.")
    st.stop()

record = row.iloc[0].to_dict()

# Show details in neat layout
left, right = st.columns(2)
with left:
    st.write("### بيانات التعريف")
    for k in ["Entity Name","Entity Code","Asset Unique No","Tag Number","Accounting Group Desc","Accounting Group Code"]:
        colname = colmap.get(k)
        if colname and colname in record and pd.notna(record[colname]):
            st.write(f"**{k}**: {record[colname]}")
    st.write("### المواصفات")
    for k in ["Description","Manufacturer","Unit of Measure","Quantity"]:
        colname = colmap.get(k)
        if colname and colname in record and pd.notna(record[colname]):
            st.write(f"**{k}**: {record[colname]}")

with right:
    st.write("### القيم المالية")
    for k in ["Cost","Depreciation Expense","Accumulated Depreciation","Residual Value","Net Book Value"]:
        colname = colmap.get(k)
        if colname and colname in record and pd.notna(record[colname]):
            st.write(f"**{k}**: {record[colname]}")
    st.write("### الموقع")
    for k in ["Country","Region","City","Building","Floor","Room/Office","Coordinates"]:
        colname = colmap.get(k)
        if colname and colname in record and pd.notna(record[colname]):
            st.write(f"**{k}**: {record[colname]}")

st.markdown("---")
st.write("### طباعة ورقة تفصيلية (PDF)")
if st.button("توليد PDF"):
    pdf_bytes = make_asset_pdf(record, colmap)
    st.success("تم إنشاء الملف.")
    st.download_button("تحميل ورقة الأصل (PDF)", data=pdf_bytes, file_name=f"asset_{selected_id}.pdf", mime="application/pdf")

st.caption("PoC — جميع الأسماء قابلة للتخصيص من utils_prepare.guess_columns().")
