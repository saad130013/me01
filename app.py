import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - بطاقات المعلومات",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات CSS مخصصة للبطاقات والجداول
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
    .asset-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #1f77b4;
        transition: transform 0.3s ease;
    }
    .asset-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .card-header {
        background: linear-gradient(135deg, #1f77b4, #2E86AB);
        color: white;
        padding: 15px;
        border-radius: 10px 10px 0 0;
        margin: -20px -20px 20px -20px;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #f0f0f0;
    }
    .info-label {
        font-weight: bold;
        color: #333;
        min-width: 200px;
    }
    .info-value {
        color: #666;
        text-align: left;
        flex-grow: 1;
    }
    .financial-value {
        background: linear-gradient(135deg, #F18F01, #FFB347);
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
    }
    .location-value {
        background: linear-gradient(135deg, #3F7CAC, #5BA8D8);
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
    }
    .section-title {
        background: linear-gradient(135deg, #A23B72, #C73E1D);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 20px 0 15px 0;
        font-weight: bold;
        text-align: center;
    }
    .quick-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .search-box {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .asset-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    @media (max-width: 768px) {
        .asset-grid {
            grid-template-columns: 1fr;
        }
        .quick-stats {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">نظام إدارة الأصول - بطاقات المعلومات التفصيلية</h1>', unsafe_allow_html=True)

# الشريط الجانبي
with st.sidebar:
    st.header("📁 تحميل البيانات")
    uploaded_file = st.file_uploader(
        "ارفع ملف Excel للسجل", 
        type=["xlsx", "xls"],
        help="يجب أن يكون الملف بصيغة Excel مع هيكل بيانات الأصول القياسي"
    )
    
    st.markdown("---")
    st.header("🎯 خيارات العرض")
    display_mode = st.radio(
        "طريقة العرض:",
        ["بطاقات تفصيلية", "جدول تقليدي", "كلا الوضعين"]
    )
    
    st.markdown("---")
    st.caption("الإصدار: 4.0 - بطاقات معلومات منظمة")

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

# قسم البحث الرئيسي
st.markdown("---")
st.markdown('<div class="search-box">', unsafe_allow_html=True)
st.subheader("🔍 البحث عن الأصول")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input(
        "ابحث برقم الأصل الفريد أو الوسم أو الوصف:",
        placeholder="أدخل رقم الأصل، الوسم، أو كلمات من الوصف..."
    )

# الحصول على أعمدة البحث
unique_asset_col = colmap.get("Asset Unique No")
tag_col = colmap.get("Tag Number")
desc_col = colmap.get("Description")
cost_col = colmap.get("Cost")
nbv_col = colmap.get("Net Book Value")
city_col = colmap.get("City")
building_col = colmap.get("Building")

with col2:
    if city_col and city_col in df.columns:
        cities = sorted([c for c in df[city_col].dropna().astype(str).unique().tolist() if c.strip()])
        selected_city = st.selectbox("المدينة", ["الكل"] + cities)
    else:
        selected_city = "الكل"

with col3:
    items_per_page = st.selectbox("عدد العناصر لكل صفحة:", [10, 25, 50, 100], index=1)

st.markdown('</div>', unsafe_allow_html=True)

# تطبيق الفلاتر
df_filtered = df.copy()

if search_query.strip():
    def advanced_search(row):
        search_terms = search_query.lower().strip()
        
        # البحث في الحقول الرئيسية
        search_fields = []
        if unique_asset_col and unique_asset_col in row:
            search_fields.append(str(row[unique_asset_col]))
        if tag_col and tag_col in row:
            search_fields.append(str(row[tag_col]))
        if desc_col and desc_col in row:
            search_fields.append(str(row[desc_col]))
        
        content = " ".join(search_fields).lower()
        return search_terms in content
    
    df_filtered = df_filtered[df_filtered.apply(advanced_search, axis=1)]

if selected_city != "الكل" and city_col and city_col in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[city_col].astype(str) == selected_city]

# الإحصائيات السريعة
total_assets = len(df_filtered)
total_cost = df_filtered[cost_col].sum() if cost_col and cost_col in df_filtered.columns else 0
total_nbv = df_filtered[nbv_col].sum() if nbv_col and nbv_col in df_filtered.columns else 0

st.markdown("---")
st.subheader("📊 نظرة سريعة على النتائج")

if total_assets == 0:
    st.warning("⚠️ لم يتم العثور على أصول تطابق معايير البحث.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0; font-size: 14px;">عدد الأصول</h3>
        <p style="margin:0; font-size: 24px; font-weight: bold;">{total_assets:,}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0; font-size: 14px;">إجمالي التكلفة</h3>
        <p style="margin:0; font-size: 18px; font-weight: bold;">{total_cost:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0; font-size: 14px;">صافي القيمة</h3>
        <p style="margin:0; font-size: 18px; font-weight: bold;">{total_nbv:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    avg_cost = total_cost / total_assets if total_assets > 0 else 0
    st.markdown(f"""
    <div class="stat-box">
        <h3 style="margin:0; font-size: 14px;">متوسط التكلفة</h3>
        <p style="margin:0; font-size: 18px; font-weight: bold;">{avg_cost:,.0f}</p>
    </div>
    """, unsafe_allow_html=True)

# دالة لإنشاء بطاقة الأصل
def create_asset_card(asset_data):
    """إنشاء بطاقة معلومات تفصيلية للأصل"""
    
    card_html = f"""
    <div class="asset-card">
        <div class="card-header">
            <h3 style="margin:0; font-size: 18px;">📋 بطاقة الأصل</h3>
        </div>
    """
    
    # المعلومات الأساسية
    card_html += """
        <div class="section-title">🆔 المعلومات الأساسية</div>
    """
    
    basic_info = [
        ("رقم الأصل الفريد", unique_asset_col),
        ("رقم الوسم", tag_col),
        ("وصف الأصل", desc_col)
    ]
    
    for label, col_name in basic_info:
        if col_name and col_name in asset_data and pd.notna(asset_data[col_name]):
            value = str(asset_data[col_name])
            card_html += f"""
            <div class="info-row">
                <span class="info-label">{label}:</span>
                <span class="info-value">{value}</span>
            </div>
            """
    
    # المعلومات المالية
    card_html += """
        <div class="section-title">💰 المعلومات المالية</div>
    """
    
    financial_info = [
        ("التكلفة", cost_col),
        ("صافي القيمة الدفترية", nbv_col)
    ]
    
    for label, col_name in financial_info:
        if col_name and col_name in asset_data and pd.notna(asset_data[col_name]):
            try:
                value = f"{float(asset_data[col_name]):,.2f}"
                card_html += f"""
                <div class="info-row">
                    <span class="info-label">{label}:</span>
                    <span class="financial-value">{value}</span>
                </div>
                """
            except:
                value = str(asset_data[col_name])
                card_html += f"""
                <div class="info-row">
                    <span class="info-label">{label}:</span>
                    <span class="info-value">{value}</span>
                </div>
                """
    
    # معلومات الموقع
    card_html += """
        <div class="section-title">📍 معلومات الموقع</div>
    """
    
    location_info = [
        ("المدينة", city_col),
        ("رقم المبنى", building_col)
    ]
    
    for label, col_name in location_info:
        if col_name and col_name in asset_data and pd.notna(asset_data[col_name]):
            value = str(asset_data[col_name])
            card_html += f"""
            <div class="info-row">
                <span class="info-label">{label}:</span>
                <span class="location-value">{value}</span>
            </div>
            """
    
    card_html += "</div>"
    return card_html

# عرض النتائج حسب طريقة العرض المختارة
st.markdown("---")
st.subheader(f"📋 نتائج البحث ({total_assets} أصل)")

# تقسيم الصفحات
if total_assets > 0:
    total_pages = (total_assets - 1) // items_per_page + 1
    current_page = st.number_input("الصفحة", min_value=1, max_value=total_pages, value=1)
    start_idx = (current_page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_assets)
    
    st.caption(f"عرض النتائج من {start_idx + 1} إلى {end_idx} من إجمالي {total_assets} أصل")

# عرض البطاقات التفصيلية
if display_mode in ["بطاقات تفصيلية", "كلا الوضعين"]:
    st.markdown("### 🎴 البطاقات التفصيلية")
    
    if total_assets > 0:
        # إنشاء شبكة البطاقات
        assets_to_display = df_filtered.iloc[start_idx:end_idx]
        
        for idx, asset in assets_to_display.iterrows():
            asset_card = create_asset_card(asset)
            st.markdown(asset_card, unsafe_allow_html=True)
            
            # أزرار إضافية لكل بطاقة
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button(f"📄 إنشاء PDF", key=f"pdf_{idx}"):
                    try:
                        pdf_bytes = make_asset_pdf(asset.to_dict(), colmap)
                        asset_id = asset[unique_asset_col] if unique_asset_col and unique_asset_col in asset else f"asset_{idx}"
                        st.download_button(
                            "⬇️ تحميل PDF",
                            data=pdf_bytes,
                            file_name=f"asset_{asset_id}.pdf",
                            mime="application/pdf",
                            key=f"dl_pdf_{idx}"
                        )
                    except Exception as e:
                        st.error(f"خطأ في إنشاء PDF: {e}")
            
            with col2:
                if st.button(f"📊 تحليل مفصل", key=f"analyze_{idx}"):
                    st.session_state[f'analyze_asset_{idx}'] = True
            
            with col3:
                if st.button(f"📍 عرض على الخريطة", key=f"map_{idx}"):
                    st.session_state[f'show_map_{idx}'] = True
            
            st.markdown("---")

# عرض الجدول التقليدي
if display_mode in ["جدول تقليدي", "كلا الوضعين"]:
    st.markdown("### 📊 عرض جدولي")
    
    # إنشاء جدول منسق
    def create_styled_table(dataframe):
        """إنشاء جدول منسق للعرض"""
        
        display_columns = []
        column_mapping = {
            "Unique Asset Number": unique_asset_col,
            "Tag number": tag_col,
            "Asset Description": desc_col,
            "Cost": cost_col,
            "Net Book Value": nbv_col,
            "City": city_col,
            "Building Number": building_col
        }
        
        for display_name, actual_col in column_mapping.items():
            if actual_col and actual_col in dataframe.columns:
                display_columns.append(actual_col)
        
        display_df = dataframe[display_columns].copy()
        
        # تنسيق الأرقام المالية
        if cost_col in display_df.columns:
            display_df[cost_col] = display_df[cost_col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "---")
        if nbv_col in display_df.columns:
            display_df[nbv_col] = display_df[nbv_col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "---")
        
        return display_df
    
    if total_assets > 0:
        display_df = create_styled_table(df_filtered.iloc[start_idx:end_idx])
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )

# قسم التصدير
st.markdown("---")
st.subheader("💾 تصدير النتائج")

col1, col2, col3 = st.columns(3)

with col1:
    # تصدير Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='الأصول')
        
        # تنسيق Excel
        workbook = writer.book
        worksheet = writer.sheets['الأصول']
        
        header_format = workbook.add_format({
            'bold': True,
            'fg_color': '#1f77b4',
            'font_color': 'white',
            'border': 1
        })
        
        for col_num, value in enumerate(df_filtered.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    excel_buffer.seek(0)
    st.download_button(
        "📥 تحميل Excel",
        data=excel_buffer,
        file_name="الأصول_المصفاة.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    # تصدير HTML
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>تقرير الأصول</title>
        <style>
            body {{ font-family: Arial, sans-serif; direction: rtl; }}
            .header {{ text-align: center; color: #1f77b4; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background-color: #1f77b4; color: white; padding: 12px; }}
            td {{ padding: 10px; border: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1 class="header">تقرير الأصول - {pd.Timestamp.now().strftime('%Y-%m-%d')}</h1>
        {df_filtered.to_html(index=False, escape=False)}
    </body>
    </html>
    """
    
    st.download_button(
        "🌐 تحميل HTML",
        data=html_content,
        file_name="تقرير_الأصول.html",
        mime="text/html",
        use_container_width=True
    )

with col3:
    # طباعة التقرير
    if st.button("🖨️ طباعة التقرير", use_container_width=True):
        st.markdown("""
        <script>
        window.print();
        </script>
        """, unsafe_allow_html=True)
        st.success("تم فتح نافذة الطباعة")

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 4.0 - بطاقات المعلومات المنظمة</h3>'
    '<p style="margin:5px 0 0 0;">عرض مرئي منظم ومهني لمعلومات الأصول</p>'
    '</div>', 
    unsafe_allow_html=True
)
