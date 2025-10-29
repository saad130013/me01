import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - النسخة المحسنة",
    layout="wide",
    initial_sidebar_state="expanded"
)

# إضافة بعض التنسيقات CSS مخصصة
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">نظام إدارة وعرض سجلات الأصول - النسخة المحسنة</h1>', unsafe_allow_html=True)

# الشريط الجانبي
with st.sidebar:
    st.header("📁 تحميل البيانات")
    uploaded_file = st.file_uploader(
        "ارفع ملف Excel للسجل", 
        type=["xlsx", "xls"],
        help="يجب أن يكون الملف بصيغة Excel مع هيكل بيانات الأصول القياسي"
    )
    
    st.markdown("---")
    st.header("⚙️ الإعدادات")
    st.caption("ملاحظة: سيقوم النظام بقراءة البيانات من الصف الثاني تلقائيًا (header=1).")
    
    # إضافة معلومات إضافية في الشريط الجانبي
    st.markdown("---")
    st.markdown("### 📊 معلومات النظام")
    st.caption("الإصدار: 2.0 - محسّن")
    st.caption("تاريخ التحديث: 2024")

# معالجة حالة عدم رفع ملف
if uploaded_file is None:
    st.info("👆 الرجاء رفع ملف السجل (Excel) لبدء استخدام النظام.")
    st.markdown("""
    ### التعليمات السريعة:
    1. قم برفع ملف Excel يحتوي على بيانات الأصول
    2. تأكد من أن البيانات تبدأ من الصف الثاني
    3. استخدم خيارات التصفية للعثور على الأصول المطلوبة
    4. اختر أصلًا معينًا لعرض تفاصيله الكاملة
    5. قم بتحميل التقارير بصيغتي Excel أو PDF
    """)
    st.stop()

# تحميل البيانات مع معالجة الأخطاء المحسنة
@st.cache_data(show_spinner="جاري تحميل البيانات...")
def load_data(uploaded_file):
    try:
        df_raw = pd.read_excel(uploaded_file, header=1)
        if df_raw.empty:
            st.error("الملف المرفوع فارغ أو لا يحتوي على بيانات.")
            return None
        return df_raw
    except Exception as e:
        st.error(f"❌ تعذر قراءة الملف: {str(e)}")
        st.info("يرجى التأكد من أن الملف بصيغة Excel صحيحة وغير تالف.")
        return None

# تحضير البيانات
@st.cache_data(show_spinner="جاري تحضير البيانات...")
def process_data(df_raw):
    try:
        df_processed = prepare_dataframe(df_raw)
        return df_processed
    except Exception as e:
        st.error(f"❌ خطأ في معالجة البيانات: {str(e)}")
        return None

# تحميل ومعالجة البيانات
with st.spinner("جاري تحميل البيانات..."):
    df_raw = load_data(uploaded_file)

if df_raw is None:
    st.stop()

with st.spinner("جاري معالجة البيانات..."):
    df = process_data(df_raw)

if df is None:
    st.stop()

# عرض إحصائيات سريعة
st.subheader("📈 نظرة عامة على البيانات")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("إجمالي السجلات", f"{len(df):,}")
with col2:
    st.metric("عدد الأعمدة", len(df.columns))
with col3:
    non_null_count = df.count().sum()
    st.metric("إجمالي القيم", f"{non_null_count:,}")
with col4:
    completeness = f"{(non_null_count / (len(df) * len(df.columns)) * 100):.1f}%"
    st.metric("نسبة اكتمال البيانات", completeness)

# تعيين الأعمدة
colmap = guess_columns(df.columns)

with st.expander("🔧 تعيين/تأكيد أسماء الأعمدة:", expanded=False):
    st.info("إذا كانت التعيينات التلقائية غير صحيحة، يرجى اختيار الأعمدة المناسبة يدويًا.")
    
    columns_mapping = {}
    for key, current_value in colmap.items():
        options = ["(غير موجود)"] + list(df.columns)
        default_index = 0
        if current_value in df.columns:
            default_index = list(df.columns).index(current_value) + 1
        
        selected_col = st.selectbox(
            f"{key}", 
            options=options,
            index=default_index,
            key=f"colmap_{key}"  # إضافة مفتاح فريد لكل selectbox
        )
        columns_mapping[key] = selected_col if selected_col != "(غير موجود)" else None
    
    colmap = columns_mapping

# قسم البحث والتصفية
st.subheader("🔍 البحث والتصفية")

# شريط البحث
search_query = st.text_input(
    "ابحث برقم الأصل/الوسم/الوصف:", 
    "",
    placeholder="أدخل كلمة للبحث في أرقام الأصول، الوسوم، والوصف..."
)

# عوامل التصفية
city_col = colmap.get("City")
cities = []
if city_col and city_col in df.columns and city_col != "(غير موجود)":
    cities = sorted([c for c in df[city_col].dropna().astype(str).unique().tolist() if c.strip()])

col1, col2, col3 = st.columns([2, 1, 1])
with col2:
    selected_city = st.selectbox("المدينة", ["الكل"] + cities) if cities else "الكل"

with col3:
    # إضافة تصفية إضافية بحسب مجموعة المحاسبة
    accounting_col = colmap.get("Accounting Group Desc")
    accounting_groups = []
    if accounting_col and accounting_col in df.columns and accounting_col != "(غير موجود)":
        accounting_groups = sorted([g for g in df[accounting_col].dropna().astype(str).unique().tolist() if g.strip()])
    
    selected_accounting = st.selectbox(
        "مجموعة المحاسبة", 
        ["الكل"] + accounting_groups
    ) if accounting_groups else "الكل"

# تطبيق الفلاتر
df_filtered = df.copy()

# دالة البحث المحسنة
def advanced_search(row):
    if not search_query.strip():
        return True
    
    search_terms = search_query.lower().strip()
    
    # البحث في الحقول الرئيسية
    search_fields = [
        str(row.get(colmap.get("Asset Unique No"), "")),
        str(row.get(colmap.get("Tag Number"), "")),
        str(row.get(colmap.get("Description"), ""))
    ]
    
    content = " ".join(search_fields).lower()
    return search_terms in content

# تطبيق الفلاتر
if search_query.strip():
    df_filtered = df_filtered[df_filtered.apply(advanced_search, axis=1)]

if selected_city != "الكل" and city_col and city_col in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[city_col].astype(str) == selected_city]

if selected_accounting != "الكل" and accounting_col and accounting_col in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[accounting_col].astype(str) == selected_accounting]

# عرض النتائج
st.subheader(f"📋 السجلات المطابقة ({len(df_filtered):,} سجل)")

if len(df_filtered) == 0:
    st.warning("⚠️ لم يتم العثور على سجلات تطابق معايير البحث.")
else:
    # تحديد عدد الصفوف المعروضة
    display_limit = st.slider("عدد السجلات المعروضة", min_value=50, max_value=500, value=200, step=50)
    
    # عرض البيانات مع تحسينات التنسيق
    st.dataframe(
        df_filtered.head(display_limit),
        use_container_width=True,
        height=400
    )
    
    # تحميل النتائج المصفاة
    st.markdown("---")
    st.subheader("💾 تحميل النتائج")
    
    excel_buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='الأصول_المصفاة')
    except Exception:
        excel_buffer = io.BytesIO()
        df_filtered.to_excel(excel_buffer, index=False)
    
    excel_buffer.seek(0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 تحميل النتائج المفلترة (Excel)",
            data=excel_buffer,
            file_name="الأصول_المصفاة.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="تحميل جميع السجلات المطابقة لمعايير البحث بصيغة Excel"
        )

# قسم تفاصيل الأصل المحدد
st.markdown("---")
st.subheader("📄 تفاصيل أصل محدد")

id_col = colmap.get("Asset Unique No")
if not id_col or id_col not in df.columns:
    st.error("⚠️ لم يتم تعيين عمود 'رقم الأصل الفريد بالجهة' بشكل صحيح.")
    st.info("يرجى تعيين عمود 'رقم الأصل الفريد بالجهة' في قسم تعيين الأعمدة.")
    st.stop()

# الحصول على قائمة الأصول المصفاة
asset_ids = df_filtered[id_col].dropna().astype(str).unique().tolist()

if not asset_ids:
    st.warning("لا توجد أصول مطابقة لمعايير البحث.")
    st.stop()

selected_asset_id = st.selectbox(
    "اختر رقم الأصل", 
    [""] + asset_ids,
    help="اختر أصلًا من القائمة لعرض تفاصيله الكاملة"
)

if not selected_asset_id:
    st.info("👈 اختر أصلًا من القائمة لعرض تفاصيله.")
    st.stop()

# استرجاع بيانات الأصل المحدد
asset_data = df[df[id_col].astype(str) == str(selected_asset_id)]

if asset_data.empty:
    st.error("❌ لم يتم العثور على البيانات الخاصة بالأصل المحدد.")
    st.stop()

record = asset_data.iloc[0].to_dict()

# عرض تفاصيل الأصل
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.write("### 🏷️ بيانات التعريف")
    identity_fields = [
        "Entity Name", "Entity Code", "Asset Unique No", 
        "Tag Number", "Accounting Group Desc", "Accounting Group Code"
    ]
    
    for field in identity_fields:
        col_name = colmap.get(field)
        if col_name and col_name in record and pd.notna(record[col_name]):
            value = record[col_name]
            st.write(f"**{field}**: {value}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.write("### ⚙️ المواصفات الفنية")
    spec_fields = ["Description", "Manufacturer", "Unit of Measure", "Quantity"]
    
    for field in spec_fields:
        col_name = colmap.get(field)
        if col_name and col_name in record and pd.notna(record[col_name]):
            value = record[col_name]
            st.write(f"**{field}**: {value}")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.write("### 💰 القيم المالية")
    financial_fields = [
        "Cost", "Depreciation Expense", "Accumulated Depreciation", 
        "Residual Value", "Net Book Value"
    ]
    
    for field in financial_fields:
        col_name = colmap.get(field)
        if col_name and col_name in record and pd.notna(record[col_name]):
            value = record[col_name]
            # تنسيق القيم المالية إذا كانت رقمية
            try:
                if isinstance(value, (int, float)):
                    value = f"{value:,.2f}"
            except:
                pass
            st.write(f"**{field}**: {value}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.write("### 📍 الموقع")
    location_fields = [
        "Country", "Region", "City", "Building", 
        "Floor", "Room/Office", "Coordinates"
    ]
    
    for field in location_fields:
        col_name = colmap.get(field)
        if col_name and col_name in record and pd.notna(record[col_name]):
            value = record[col_name]
            st.write(f"**{field}**: {value}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# خريطة الموقع
coords_col = colmap.get("Coordinates")
if coords_col and coords_col in record and isinstance(record[coords_col], str):
    lat, lon = parse_coordinates(record[coords_col])
    if lat is not None and lon is not None:
        st.subheader("🗺️ موقع الأصل")
        
        try:
            fig, ax = plt.subplots(figsize=(4, 4))
            ax.scatter([lon], [lat], s=100, color='red', alpha=0.7)
            ax.set_xlabel("خط الطول (Longitude)")
            ax.set_ylabel("خط العرض (Latitude)")
            ax.set_title("الموقع التقريبي للأصل")
            ax.grid(True, alpha=0.3)
            
            # إضافة هامش حول النقطة
            margin = 0.02
            ax.set_xlim(lon - margin, lon + margin)
            ax.set_ylim(lat - margin, lat + margin)
            
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"تعذر عرض الخريطة: {str(e)}")

# قسم إنشاء التقارير
st.markdown("---")
st.subheader("📄 تقارير قابلة للطباعة")

col1, col2 = st.columns(2)

with col1:
    if st.button("🖨️ توليد تقرير PDF", type="primary", use_container_width=True):
        with st.spinner("جاري إنشاء التقرير..."):
            try:
                pdf_bytes = make_asset_pdf(record, colmap)
                st.success("✅ تم إنشاء التقرير بنجاح!")
                
                st.download_button(
                    "📥 تحميل ورقة الأصل (PDF)",
                    data=pdf_bytes,
                    file_name=f"ورقة_الأصل_{selected_asset_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ فشل في إنشاء التقرير: {str(e)}")

with col2:
    # زر لتصدير جميع البيانات
    all_data_buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(all_data_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='جميع_البيانات')
            df_filtered.to_excel(writer, index=False, sheet_name='البيانات_المصفاة')
    except Exception:
        all_data_buffer = io.BytesIO()
        with pd.ExcelWriter(all_data_buffer) as writer:
            df.to_excel(writer, index=False, sheet_name='جميع_البيانات')
            df_filtered.to_excel(writer, index=False, sheet_name='البيانات_المصفاة')
    
    all_data_buffer.seek(0)
    
    st.download_button(
        "📊 تحميل جميع البيانات (Excel)",
        data=all_data_buffer,
        file_name="جميع_بيانات_الأصول.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        help="تحميل جميع البيانات مع ورقة إضافية للبيانات المصفاة"
    )

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div class="success-box">'
    '✅ <strong>الإصدار المحسّن</strong> - تم التصحيح والتحسين بواسطة مبرمج محترف'
    '</div>', 
    unsafe_allow_html=True
)
