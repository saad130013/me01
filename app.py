import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - التصنيفات المتعددة",
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
        text-align: center;
    }
    .category-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .summary-box {
        background-color: #f8f9fa;
        border-left: 5px solid #1f77b4;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .category-level-1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .category-level-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .category-level-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .total-card { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); color: #333; }
    .progress-bar {
        height: 8px;
        background-color: #e9ecef;
        border-radius: 4px;
        margin: 5px 0;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #11998e, #38ef7d);
        border-radius: 4px;
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

st.markdown('<h1 class="main-header">نظام إدارة الأصول - التصنيفات المتعددة والإحصائيات</h1>', unsafe_allow_html=True)

# الشريط الجانبي
with st.sidebar:
    st.header("📁 تحميل البيانات")
    uploaded_file = st.file_uploader(
        "ارفع ملف Excel للسجل", 
        type=["xlsx", "xls"],
        help="يجب أن يكون الملف بصيغة Excel مع هيكل بيانات الأصول القياسي"
    )
    
    st.markdown("---")
    st.header("🎨 خيارات التصنيف")
    
    # إعدادات التصنيفات
    enable_categories = st.checkbox("تفعيل نظام التصنيفات المتعددة", value=True)
    
    if enable_categories:
        st.subheader("إعدادات التصنيفات")
        category_levels = st.slider("عدد مستويات التصنيف", 1, 3, 2)
        
    st.markdown("---")
    st.caption("الإصدار: 3.0 - التصنيفات المتعددة")

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

# قسم نظام التصنيفات المتعددة
if enable_categories:
    st.markdown("---")
    st.subheader("🏷️ نظام التصنيفات المتعددة للأصول")
    
    # تحديد أعمدة التصنيف
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_col_1 = st.selectbox(
            "التصنيف الأول (مستوى رئيسي)",
            options=["(غير محدد)"] + list(df.columns),
            index=0,
            key="cat1"
        )
    
    with col2:
        category_col_2 = st.selectbox(
            "التصنيف الثاني (مستوى فرعي)",
            options=["(غير محدد)"] + list(df.columns),
            index=0,
            key="cat2"
        ) if category_levels >= 2 else None
    
    with col3:
        category_col_3 = st.selectbox(
            "التصنيف الثالث (مستوى تفصيلي)",
            options=["(غير محدد)"] + list(df.columns),
            index=0,
            key="cat3"
        ) if category_levels >= 3 else None
    
    # تحليل التصنيفات وعرض الإحصائيات
    if category_col_1 != "(غير محدد)":
        st.markdown("---")
        st.subheader("📊 إحصائيات التصنيفات")
        
        # حساب الإحصائيات بناءً على مستويات التصنيف
        cost_col = colmap.get("Cost")
        nbv_col = colmap.get("Net Book Value")
        
        def calculate_category_stats(df, level1_col, level2_col=None, level3_col=None):
            """حساب إحصائيات التصنيفات"""
            stats = []
            
            if level2_col and level2_col != "(غير محدد)":
                # تحليل بمستويين
                grouped = df.groupby([level1_col, level2_col])
                for (cat1, cat2), group in grouped:
                    total_assets = len(group)
                    total_cost = group[cost_col].sum() if cost_col and cost_col in group.columns else 0
                    total_nbv = group[nbv_col].sum() if nbv_col and nbv_col in group.columns else 0
                    
                    stats.append({
                        'level1': cat1,
                        'level2': cat2,
                        'level3': '',
                        'total_assets': total_assets,
                        'total_cost': total_cost,
                        'total_nbv': total_nbv
                    })
            else:
                # تحليل بمستوى واحد
                grouped = df.groupby(level1_col)
                for cat1, group in grouped:
                    total_assets = len(group)
                    total_cost = group[cost_col].sum() if cost_col and cost_col in group.columns else 0
                    total_nbv = group[nbv_col].sum() if nbv_col and nbv_col in group.columns else 0
                    
                    stats.append({
                        'level1': cat1,
                        'level2': '',
                        'level3': '',
                        'total_assets': total_assets,
                        'total_cost': total_cost,
                        'total_nbv': total_nbv
                    })
            
            return pd.DataFrame(stats)
        
        # حساب الإحصائيات
        category_stats = calculate_category_stats(
            df, 
            category_col_1, 
            category_col_2 if category_levels >= 2 else None,
            category_col_3 if category_levels >= 3 else None
        )
        
        # عرض الإحصائيات في بطاقات
        if not category_stats.empty:
            # إجماليات عامة
            total_all_assets = len(df)
            total_all_cost = df[cost_col].sum() if cost_col and cost_col in df.columns else 0
            total_all_nbv = df[nbv_col].sum() if nbv_col and nbv_col in df.columns else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="total-card">
                    <h3 style="margin:0; font-size: 14px;">إجمالي الأصول</h3>
                    <p style="margin:0; font-size: 24px; font-weight: bold;">{total_all_assets:,}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="total-card">
                    <h3 style="margin:0; font-size: 14px;">إجمالي التكلفة</h3>
                    <p style="margin:0; font-size: 20px; font-weight: bold;">{total_all_cost:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="total-card">
                    <h3 style="margin:0; font-size: 14px;">صافي القيمة الدفترية</h3>
                    <p style="margin:0; font-size: 20px; font-weight: bold;">{total_all_nbv:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                unique_categories = category_stats['level1'].nunique()
                st.markdown(f"""
                <div class="total-card">
                    <h3 style="margin:0; font-size: 14px;">عدد التصنيفات</h3>
                    <p style="margin:0; font-size: 24px; font-weight: bold;">{unique_categories}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.subheader("📈 تفصيل التصنيفات")
            
            # عرض التصنيفات في أقسام منظمة
            unique_level1 = category_stats['level1'].unique()
            
            for i, level1_cat in enumerate(unique_level1):
                level1_data = category_stats[category_stats['level1'] == level1_cat]
                level1_assets = level1_data['total_assets'].sum()
                level1_cost = level1_data['total_cost'].sum()
                level1_nbv = level1_data['total_nbv'].sum()
                
                # حساب النسب المئوية
                assets_percentage = (level1_assets / total_all_assets) * 100
                cost_percentage = (level1_cost / total_all_cost) * 100 if total_all_cost > 0 else 0
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"""
                    <div class="category-level-1" style="padding: 15px; border-radius: 10px; color: white; text-align: center;">
                        <h3 style="margin:0; font-size: 16px;">{level1_cat}</h3>
                        <p style="margin:5px 0; font-size: 24px; font-weight: bold;">{level1_assets:,}</p>
                        <p style="margin:0; font-size: 12px;">أصل</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.write(f"**التكلفة الإجمالية:** {level1_cost:,.2f}")
                    st.write(f"**صافي القيمة الدفترية:** {level1_nbv:,.2f}")
                    
                    # أشرطة التقدم
                    st.write("**نسبة عدد الأصول:**")
                    st.markdown(f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {assets_percentage}%"></div>
                    </div>
                    <div style="text-align: left; font-size: 12px; color: #666;">
                        {assets_percentage:.1f}% من إجمالي الأصول
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("**نسبة التكلفة:**")
                    st.markdown(f"""
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {cost_percentage}%"></div>
                    </div>
                    <div style="text-align: left; font-size: 12px; color: #666;">
                        {cost_percentage:.1f}% من إجمالي التكلفة
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
        
        # تصفية البيانات حسب التصنيف
        st.subheader("🔍 تصفية البيانات حسب التصنيف")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_cat1 = st.selectbox(
                "اختر التصنيف الأول",
                options=["الكل"] + list(df[category_col_1].dropna().unique()),
                key="filter_cat1"
            )
        
        with col2:
            if category_col_2 and category_col_2 != "(غير محدد)":
                available_cat2 = ["الكل"]
                if selected_cat1 != "الكل":
                    available_cat2.extend(list(df[df[category_col_1] == selected_cat1][category_col_2].dropna().unique()))
                
                selected_cat2 = st.selectbox(
                    "اختر التصنيف الثاني",
                    options=available_cat2,
                    key="filter_cat2"
                )
            else:
                selected_cat2 = "الكل"
        
        with col3:
            if category_col_3 and category_col_3 != "(غير محدد)" and selected_cat2 != "الكل":
                available_cat3 = ["الكل"]
                if selected_cat1 != "الكل" and selected_cat2 != "الكل":
                    filtered_df = df[df[category_col_1] == selected_cat1]
                    filtered_df = filtered_df[filtered_df[category_col_2] == selected_cat2]
                    available_cat3.extend(list(filtered_df[category_col_3].dropna().unique()))
                
                selected_cat3 = st.selectbox(
                    "اختر التصنيف الثالث",
                    options=available_cat3,
                    key="filter_cat3"
                )
            else:
                selected_cat3 = "الكل"
        
        # تطبيق التصفية
        df_filtered = df.copy()
        
        if selected_cat1 != "الكل":
            df_filtered = df_filtered[df_filtered[category_col_1] == selected_cat1]
        
        if selected_cat2 != "الكل" and category_col_2 and category_col_2 != "(غير محدد)":
            df_filtered = df_filtered[df_filtered[category_col_2] == selected_cat2]
        
        if selected_cat3 != "الكل" and category_col_3 and category_col_3 != "(غير محدد)":
            df_filtered = df_filtered[df_filtered[category_col_3] == selected_cat3]
        
        st.success(f"تم العثور على {len(df_filtered):,} أصل في التصنيف المحدد")
        
    else:
        st.warning("⚠️ الرجاء تحديد عمود التصنيف الأول على الأقل")
        df_filtered = df.copy()
else:
    df_filtered = df.copy()

# قسم البحث والتصفية الإضافية
st.markdown("---")
st.subheader("🔍 البحث والتصفية المتقدمة")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input("ابحث برقم الأصل/الوسم/الوصف:", "")

city_col = colmap.get("City")
cities = []
if city_col and city_col in df.columns:
    cities = sorted([c for c in df[city_col].dropna().astype(str).unique().tolist() if c.strip()])

with col2:
    selected_city = st.selectbox("المدينة", ["الكل"] + cities) if cities else "الكل"

# تطبيق فلاتر البحث
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
st.subheader(f"📋 السجلات المطابقة ({len(df_filtered):,} سجل)")

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
        
        # إضافة أعمدة التصنيف إذا كانت محددة
        if enable_categories and category_col_1 != "(غير محدد)":
            important_columns.insert(0, category_col_1)
        
        if enable_categories and category_col_2 and category_col_2 != "(غير محدد)":
            important_columns.insert(1, category_col_2)
        
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
                elif col == category_col_1:
                    cell_class = "class='category-level-1'"
                elif col == category_col_2:
                    cell_class = "class='category-level-2'"
                
                html += f"<td {cell_class}>{value}</td>"
            
            html += "</tr>"
        
        html += "</tbody></table></div>"
        return html
    
    # عرض الجدول المنسق
    st.markdown(create_styled_table(df_filtered), unsafe_allow_html=True)
    
    # أزرار التحكم
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🖨️ طباعة التقرير", use_container_width=True):
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

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 3.0 - نظام التصنيفات المتعددة</h3>'
    '<p style="margin:5px 0 0 0;">تحليل إحصائي متقدم وتصنيفات متعددة المستويات</p>'
    '</div>', 
    unsafe_allow_html=True
)
