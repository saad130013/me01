import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - تقارير جدولية",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات CSS مخصصة للجداول والطباعة
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 1rem;
    }
    .print-table {
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: 12px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .print-table th {
        background-color: #2E86AB;
        color: white;
        padding: 12px 8px;
        text-align: right;
        border: 1px solid #1f77b4;
        font-weight: bold;
    }
    .print-table td {
        padding: 10px 8px;
        border: 1px solid #ddd;
        text-align: right;
    }
    .print-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .print-table tr:hover {
        background-color: #e9ecef;
    }
    .section-header {
        background-color: #A23B72 !important;
        color: white !important;
        font-size: 14px !important;
        font-weight: bold !important;
    }
    .financial-value {
        background-color: #F18F01 !important;
        color: white !important;
        font-weight: bold !important;
    }
    .important-field {
        background-color: #C73E1D !important;
        color: white !important;
    }
    .location-field {
        background-color: #3F7CAC !important;
        color: white !important;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .summary-box {
        background-color: #f8f9fa;
        border-left: 5px solid #1f77b4;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    @media print {
        .no-print {
            display: none !important;
        }
        .print-table {
            box-shadow: none !important;
        }
        body {
            zoom: 85%;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">نظام إدارة الأصول - تقارير جدولية قابلة للطباعة</h1>', unsafe_allow_html=True)

# الشريط الجانبي
with st.sidebar:
    st.header("📁 تحميل البيانات")
    uploaded_file = st.file_uploader(
        "ارفع ملف Excel للسجل", 
        type=["xlsx", "xls"],
        help="يجب أن يكون الملف بصيغة Excel مع هيكل بيانات الأصول القياسي"
    )
    
    st.markdown("---")
    st.header("🎨 خيارات التنسيق")
    table_style = st.selectbox(
        "نمط الجدول",
        ["نمط افتراضي", "نمط مدمج", "نمط متعدد الألوان", "نمط للطباعة"]
    )
    
    show_images = st.checkbox("إظهار الأيقونات", value=True)
    st.markdown("---")
    st.caption("الإصدار: 2.1 - جداول قابلة للطباعة")

# معالجة حالة عدم رفع ملف
if uploaded_file is None:
    st.info("👆 الرجاء رفع ملف السجل (Excel) لبدء استخدام النظام.")
    st.stop()

# تحميل البيانات
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

# تعيين الأعمدة
colmap = guess_columns(df.columns)

# قسم البحث والتصفية
st.subheader("🔍 البحث والتصفية")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input("ابحث برقم الأصل/الوسم/الوصف:", "")

city_col = colmap.get("City")
cities = []
if city_col and city_col in df.columns:
    cities = sorted([c for c in df[city_col].dropna().astype(str).unique().tolist() if c.strip()])

with col2:
    selected_city = st.selectbox("المدينة", ["الكل"] + cities) if cities else "الكل"

# تطبيق الفلاتر
df_filtered = df.copy()

if search_query.strip():
    def search_function(row):
        search_fields = [
            str(row.get(colmap.get("Asset Unique No"), "")),
            str(row.get(colmap.get("Tag Number"), "")),
            str(row.get(colmap.get("Description"), ""))
        ]
        content = " ".join(search_fields).lower()
        return search_query.lower() in content
    
    df_filtered = df_filtered[df_filtered.apply(search_function, axis=1)]

if selected_city != "الكل" and city_col and city_col in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[city_col].astype(str) == selected_city]

# عرض النتائج في جدول منسق
st.subheader(f"📊 السجلات المطابقة ({len(df_filtered):,} سجل)")

if len(df_filtered) == 0:
    st.warning("⚠️ لم يتم العثور على سجلات تطابق معايير البحث.")
else:
    # إنشاء جدول منسق للعرض
    def create_styled_table(dataframe, max_rows=100):
        """إنشاء جدول منسق مع ألوان وتصنيفات"""
        
        # تحديد الأعمدة المهمة للعرض
        important_columns = []
        for col_key in ["Asset Unique No", "Tag Number", "Description", "Cost", "Net Book Value", "City", "Building"]:
            col_name = colmap.get(col_key)
            if col_name and col_name in dataframe.columns:
                important_columns.append(col_name)
        
        # إذا كانت الأعمدة المهمة أقل من 4، أضف أعمدة إضافية
        if len(important_columns) < 4:
            additional_cols = [col for col in dataframe.columns if col not in important_columns][:6]
            important_columns.extend(additional_cols)
        
        display_df = dataframe[important_columns].head(max_rows)
        
        # إنشاء HTML للجدول المنسق
        html = f"""
        <div style="overflow-x: auto; margin: 20px 0;">
            <table class="print-table">
                <thead>
                    <tr>
        """
        
        # رؤوس الأعمدة
        for col in display_df.columns:
            html += f'<th>{col}</th>'
        html += "</tr></thead><tbody>"
        
        # بيانات الصفوف
        for idx, row in display_df.iterrows():
            html += "<tr>"
            for col in display_df.columns:
                value = row[col]
                cell_class = ""
                
                # تحديد لون الخلية بناءً على نوع البيانات
                if pd.isna(value):
                    value = "---"
                    cell_class = "style='background-color: #f8d7da; color: #721c24;'"
                elif col == colmap.get("Cost") or col == colmap.get("Net Book Value"):
                    try:
                        num_value = float(value)
                        value = f"{num_value:,.2f}"
                        cell_class = "class='financial-value'"
                    except:
                        pass
                elif col == colmap.get("Asset Unique No") or col == colmap.get("Tag Number"):
                    cell_class = "class='important-field'"
                elif col == colmap.get("City") or col == colmap.get("Building"):
                    cell_class = "class='location-field'"
                
                html += f"<td {cell_class}>{value}</td>"
            
            html += "</tr>"
        
        html += "</tbody></table></div>"
        return html
    
    # عرض الجدول المنسق
    st.markdown(create_styled_table(df_filtered), unsafe_allow_html=True)
    
    # أزرار التحكم
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🖨️ طباعة الجدول", use_container_width=True):
            st.markdown("""
            <script>
            window.print();
            </script>
            """, unsafe_allow_html=True)
            st.success("تم فتح نافذة الطباعة")
    
    with col2:
        # تحميل كـ HTML
        html_content = create_styled_table(df_filtered, max_rows=1000)
        st.download_button(
            "📥 تحميل كـ HTML",
            data=html_content,
            file_name="الجدول_المنسق.html",
            mime="text/html",
            use_container_width=True
        )
    
    with col3:
        # تحميل كـ Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='البيانات')
            
            # إضافة تنسيقات إلى Excel
            workbook = writer.book
            worksheet = writer.sheets['البيانات']
            
            # تنسيق الرؤوس
            header_format = workbook.add_format({
                'bold': True,
                'fg_color': '#2E86AB',
                'font_color': 'white',
                'border': 1
            })
            
            for col_num, value in enumerate(df_filtered.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        excel_buffer.seek(0)
        st.download_button(
            "📊 تحميل كـ Excel",
            data=excel_buffer,
            file_name="البيانات_المنسقة.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# قسم التفاصيل المفصلة للأصل المحدد
st.markdown("---")
st.subheader("📄 تقرير مفصل لأصل محدد")

id_col = colmap.get("Asset Unique No")
if not id_col or id_col not in df.columns:
    st.error("⚠️ لم يتم تعيين عمود 'رقم الأصل الفريد' بشكل صحيح.")
    st.stop()

asset_ids = df_filtered[id_col].dropna().astype(str).unique().tolist()

if asset_ids:
    selected_asset_id = st.selectbox("اختر رقم الأصل", [""] + asset_ids)
    
    if selected_asset_id:
        asset_data = df[df[id_col].astype(str) == str(selected_asset_id)]
        
        if not asset_data.empty:
            record = asset_data.iloc[0].to_dict()
            
            # إنشاء تقرير مفصل منسق
            def create_detailed_report(record_data, column_mapping):
                """إنشاء تقرير مفصل منسق للطباعة"""
                
                report_html = """
                <div style="font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; border: 2px solid #1f77b4; border-radius: 10px;">
                    <div style="text-align: center; background: linear-gradient(135deg, #1f77b4, #2E86AB); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                        <h1 style="margin: 0; font-size: 28px;">تقرير مفصل عن الأصل</h1>
                        <h2 style="margin: 10px 0 0 0; font-size: 22px;">نظام إدارة الأصول</h2>
                    </div>
                """
                
                # معلومات التعريف
                report_html += """
                <div style="margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                """
                
                sections = [
                    {
                        "title": "🆔 بيانات التعريف الأساسية",
                        "fields": ["Entity Name", "Entity Code", "Asset Unique No", "Tag Number", "Accounting Group Desc", "Accounting Group Code"]
                    },
                    {
                        "title": "⚙️ المواصفات الفنية",
                        "fields": ["Description", "Manufacturer", "Unit of Measure", "Quantity"]
                    },
                    {
                        "title": "💰 المعلومات المالية",
                        "fields": ["Cost", "Depreciation Expense", "Accumulated Depreciation", "Residual Value", "Net Book Value"]
                    },
                    {
                        "title": "📍 بيانات الموقع",
                        "fields": ["Country", "Region", "City", "Building", "Floor", "Room/Office", "Coordinates"]
                    }
                ]
                
                for section in sections:
                    report_html += f"""
                    <tr>
                        <td colspan="2" style="background-color: #A23B72; color: white; padding: 12px; font-weight: bold; font-size: 16px; text-align: center;">
                            {section['title']}
                        </td>
                    </tr>
                    """
                    
                    for field in section['fields']:
                        col_name = column_mapping.get(field)
                        if col_name and col_name in record_data:
                            value = record_data[col_name]
                            if pd.notna(value):
                                # تنسيق القيم المالية
                                if field in ["Cost", "Depreciation Expense", "Accumulated Depreciation", "Residual Value", "Net Book Value"]:
                                    try:
                                        value = f"{float(value):,.2f}"
                                    except:
                                        pass
                                
                                report_html += f"""
                                <tr>
                                    <td style="background-color: #f8f9fa; padding: 10px; border: 1px solid #ddd; font-weight: bold; width: 30%;">
                                        {field}
                                    </td>
                                    <td style="padding: 10px; border: 1px solid #ddd; width: 70%;">
                                        {value}
                                    </td>
                                </tr>
                                """
                
                report_html += """
                    </table>
                </div>
                <div style="text-align: center; margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 0 0 8px 8px;">
                    <p style="margin: 0; color: #666;">تم إنشاء هذا التقرير تلقائيًا من نظام إدارة الأصول</p>
                </div>
                </div>
                """
                
                return report_html
            
            # عرض التقرير المفصل
            detailed_report = create_detailed_report(record, colmap)
            st.markdown(detailed_report, unsafe_allow_html=True)
            
            # أزرار تحميل التقرير
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🖨️ طباعة التقرير المفصل", use_container_width=True):
                    st.markdown("""
                    <script>
                    window.print();
                    </script>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.download_button(
                    "📥 تحميل التقرير كـ HTML",
                    data=detailed_report,
                    file_name=f"تقرير_الأصل_{selected_asset_id}.html",
                    mime="text/html",
                    use_container_width=True
                )

# ملخص إحصائي
st.markdown("---")
st.subheader("📈 ملخص إحصائي")

if len(df_filtered) > 0:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_assets = len(df_filtered)
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; font-size: 14px;">إجمالي الأصول</h3>
            <p style="margin:0; font-size: 24px; font-weight: bold;">{total_assets:,}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        cost_col = colmap.get("Cost")
        total_cost = 0
        if cost_col and cost_col in df_filtered.columns:
            total_cost = df_filtered[cost_col].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; font-size: 14px;">إجمالي التكلفة</h3>
            <p style="margin:0; font-size: 20px; font-weight: bold;">{total_cost:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        nbv_col = colmap.get("Net Book Value")
        total_nbv = 0
        if nbv_col and nbv_col in df_filtered.columns:
            total_nbv = df_filtered[nbv_col].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; font-size: 14px;">صافي القيمة الدفترية</h3>
            <p style="margin:0; font-size: 20px; font-weight: bold;">{total_nbv:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if city_col and city_col in df_filtered.columns:
            cities_count = df_filtered[city_col].nunique()
            st.markdown(f"""
            <div class="metric-card">
                <h3 style="margin:0; font-size: 14px;">عدد المدن</h3>
                <p style="margin:0; font-size: 24px; font-weight: bold;">{cities_count}</p>
            </div>
            """, unsafe_allow_html=True)

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار المحسّن - جداول قابلة للطباعة</h3>'
    '<p style="margin:5px 0 0 0;">تم التصميم خصيصًا للعرض والطباعة بشكل أنيق ومهني</p>'
    '</div>', 
    unsafe_allow_html=True
)
