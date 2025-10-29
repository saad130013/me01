import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - تقارير متكاملة",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات CSS مخصصة للبطاقات والجداول والطباعة
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
    .location-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin: 10px 0;
    }
    .location-item {
        background: linear-gradient(135deg, #3F7CAC, #5BA8D8);
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
    }
    .printable-table {
        border-collapse: collapse;
        width: 100%;
        font-family: Arial, sans-serif;
        font-size: 12px;
    }
    .printable-table th {
        background-color: #1f77b4;
        color: white;
        padding: 12px 8px;
        text-align: center;
        border: 1px solid #1f77b4;
        font-weight: bold;
    }
    .printable-table td {
        padding: 10px 8px;
        border: 1px solid #ddd;
        text-align: center;
    }
    .printable-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    @media print {
        .no-print {
            display: none !important;
        }
        .printable-table {
            font-size: 10px;
        }
        body {
            zoom: 80%;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">نظام إدارة الأصول - تقارير متكاملة</h1>', unsafe_allow_html=True)

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
    st.caption("الإصدار: 5.1 - تقارير HTML قابلة للطباعة")

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
unique_asset_col = colmap.get("Asset Unique No") or "Unique Asset Number in the entity"
tag_col = colmap.get("Tag Number") or "Tag number"
desc_col = colmap.get("Description") or "Asset Description"
cost_col = colmap.get("Cost") or "Cost"
nbv_col = colmap.get("Net Book Value") or "Net Book Value"
city_col = colmap.get("City") or "City"

# أعمدة الموقع التفصيلية
building_col = colmap.get("Building") or "Building Numbe"
floor_col = colmap.get("Floor") or "Floor"
room_col = colmap.get("Room/Office") or "Room/Office"

with col2:
    if city_col in df.columns:
        cities = sorted([str(c) for c in df[city_col].dropna().unique().tolist() if pd.notna(c) and str(c).strip()])
        selected_city = st.selectbox("المدينة", ["الكل"] + cities)
    else:
        selected_city = "الكل"
        st.info("عمود المدينة غير موجود")

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
        if unique_asset_col in row and pd.notna(row[unique_asset_col]):
            search_fields.append(str(row[unique_asset_col]))
        if tag_col in row and pd.notna(row[tag_col]):
            search_fields.append(str(row[tag_col]))
        if desc_col in row and pd.notna(row[desc_col]):
            search_fields.append(str(row[desc_col]))
        
        content = " ".join(search_fields).lower()
        return search_terms in content
    
    df_filtered = df_filtered[df_filtered.apply(advanced_search, axis=1)]

if selected_city != "الكل" and city_col in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[city_col].astype(str) == selected_city]

# الإحصائيات السريعة
total_assets = len(df_filtered)
total_cost = df_filtered[cost_col].sum() if cost_col in df_filtered.columns else 0
total_nbv = df_filtered[nbv_col].sum() if nbv_col in df_filtered.columns else 0

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

# دالة لإنشاء تقرير HTML شامل
def create_html_report(assets_data, report_type="تقرير شامل"):
    """إنشاء تقرير HTML شامل قابل للطباعة"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>{report_type} - نظام إدارة الأصول</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                margin: 20px;
                line-height: 1.6;
                color: #333;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #1f77b4, #2E86AB);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .report-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                border-right: 4px solid #1f77b4;
            }}
            .printable-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 12px;
            }}
            .printable-table th {{
                background-color: #1f77b4;
                color: white;
                padding: 12px 8px;
                text-align: center;
                border: 1px solid #1f77b4;
                font-weight: bold;
            }}
            .printable-table td {{
                padding: 10px 8px;
                border: 1px solid #ddd;
                text-align: center;
            }}
            .printable-table tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            .printable-table tr:hover {{
                background-color: #e9ecef;
            }}
            .financial-cell {{
                background-color: #fff3cd;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                font-size: 12px;
                color: #666;
            }}
            @media print {{
                body {{
                    margin: 0;
                    padding: 20px;
                }}
                .printable-table {{
                    font-size: 10px;
                }}
                .no-print {{
                    display: none;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{report_type}</h1>
            <h2>نظام إدارة الأصول</h2>
        </div>
        
        <div class="report-info">
            <p><strong>تاريخ التقرير:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d')}</p>
            <p><strong>عدد الأصول:</strong> {len(assets_data):,}</p>
            <p><strong>إجمالي التكلفة:</strong> {total_cost:,.2f}</p>
            <p><strong>صافي القيمة الدفترية:</strong> {total_nbv:,.2f}</p>
        </div>
    """
    
    if report_type == "تقرير إحصائي":
        # إحصائيات حسب المدينة
        if city_col in assets_data.columns:
            city_stats = assets_data.groupby(city_col).agg({
                cost_col: 'sum',
                nbv_col: 'sum',
                unique_asset_col: 'count'
            }).reset_index()
            
            html_content += """
            <h3 style="text-align: center; color: #1f77b4;">الإحصائيات حسب المدينة</h3>
            <table class="printable-table">
                <thead>
                    <tr>
                        <th>المدينة</th>
                        <th>عدد الأصول</th>
                        <th>إجمالي التكلفة</th>
                        <th>صافي القيمة</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, row in city_stats.iterrows():
                html_content += f"""
                    <tr>
                        <td>{row[city_col]}</td>
                        <td>{row[unique_asset_col]:,}</td>
                        <td class="financial-cell">{row[cost_col]:,.2f}</td>
                        <td class="financial-cell">{row[nbv_col]:,.2f}</td>
                    </tr>
                """
            
            html_content += """
                </tbody>
            </table>
            """
    else:
        # جدول البيانات التفصيلي
        display_columns = [
            unique_asset_col, tag_col, desc_col, 
            cost_col, nbv_col, city_col,
            building_col, floor_col, room_col
        ]
        
        available_columns = [col for col in display_columns if col in assets_data.columns]
        
        if available_columns:
            headers = {
                unique_asset_col: 'رقم الأصل',
                tag_col: 'رقم الوسم',
                desc_col: 'الوصف',
                cost_col: 'التكلفة',
                nbv_col: 'صافي القيمة',
                city_col: 'المدينة',
                building_col: 'رقم المبنى',
                floor_col: 'الدور',
                room_col: 'الغرفة'
            }
            
            html_content += f"""
            <h3 style="text-align: center; color: #1f77b4;">البيانات التفصيلية للأصول</h3>
            <table class="printable-table">
                <thead>
                    <tr>
            """
            
            for col in available_columns:
                html_content += f"<th>{headers.get(col, col)}</th>"
            
            html_content += """
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, asset in assets_data.iterrows():
                html_content += "<tr>"
                for col in available_columns:
                    value = asset[col]
                    if pd.isna(value):
                        html_content += "<td>---</td>"
                    elif col in [cost_col, nbv_col]:
                        try:
                            html_content += f"<td class='financial-cell'>{float(value):,.2f}</td>"
                        except:
                            html_content += f"<td>{value}</td>"
                    else:
                        if col == desc_col and len(str(value)) > 50:
                            html_content += f"<td>{str(value)[:50]}...</td>"
                        else:
                            html_content += f"<td>{value}</td>"
                html_content += "</tr>"
            
            html_content += """
                </tbody>
            </table>
            """
    
    html_content += f"""
        <div class="footer">
            <p>تم إنشاء هذا التقرير تلقائياً بواسطة نظام إدارة الأصول</p>
            <p>تاريخ الإنشاء: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <div class="no-print" style="text-align: center; margin-top: 20px;">
            <button onclick="window.print()" style="padding: 10px 20px; background: #1f77b4; color: white; border: none; border-radius: 5px; cursor: pointer;">🖨️ طباعة التقرير</button>
        </div>
    </body>
    </html>
    """
    
    return html_content

# دالة لعرض بطاقة الأصل
def display_asset_card(asset_data):
    """عرض بطاقة معلومات تفصيلية للأصل"""
    
    with st.container():
        st.markdown("---")
        
        # رأس البطاقة
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #1f77b4, #2E86AB); color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">'
                f'<h3 style="margin:0; font-size: 18px;">📋 بطاقة الأصل</h3>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        # المعلومات الأساسية
        st.markdown(
            '<div style="background: linear-gradient(135deg, #A23B72, #C73E1D); color: white; padding: 12px; border-radius: 8px; margin: 20px 0 15px 0; font-weight: bold; text-align: center;">'
            '🆔 المعلومات الأساسية'
            '</div>',
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if unique_asset_col in asset_data and pd.notna(asset_data[unique_asset_col]):
                st.metric("رقم الأصل الفريد", str(asset_data[unique_asset_col]))
        
        with col2:
            if tag_col in asset_data and pd.notna(asset_data[tag_col]):
                st.metric("رقم الوسم", str(asset_data[tag_col]))
        
        with col3:
            if desc_col in asset_data and pd.notna(asset_data[desc_col]):
                description = str(asset_data[desc_col])
                if len(description) > 50:
                    description = description[:50] + "..."
                st.metric("وصف الأصل", description)
        
        # المعلومات المالية
        st.markdown(
            '<div style="background: linear-gradient(135deg, #A23B72, #C73E1D); color: white; padding: 12px; border-radius: 8px; margin: 20px 0 15px 0; font-weight: bold; text-align: center;">'
            '💰 المعلومات المالية'
            '</div>',
            unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if cost_col in asset_data and pd.notna(asset_data[cost_col]):
                try:
                    cost_value = f"{float(asset_data[cost_col]):,.2f}"
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, #F18F01, #FFB347); color: white; padding: 15px; border-radius: 10px; text-align: center;">'
                        f'<h4 style="margin:0; font-size: 14px;">التكلفة</h4>'
                        f'<p style="margin:0; font-size: 18px; font-weight: bold;">{cost_value}</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                except:
                    st.info(f"التكلفة: {asset_data[cost_col]}")
        
        with col2:
            if nbv_col in asset_data and pd.notna(asset_data[nbv_col]):
                try:
                    nbv_value = f"{float(asset_data[nbv_col]):,.2f}"
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, #F18F01, #FFB347); color: white; padding: 15px; border-radius: 10px; text-align: center;">'
                        f'<h4 style="margin:0; font-size: 14px;">صافي القيمة الدفترية</h4>'
                        f'<p style="margin:0; font-size: 18px; font-weight: bold;">{nbv_value}</p>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                except:
                    st.info(f"صافي القيمة: {asset_data[nbv_col]}")
        
        # معلومات الموقع التفصيلية
        st.markdown(
            '<div style="background: linear-gradient(135deg, #A23B72, #C73E1D); color: white; padding: 12px; border-radius: 8px; margin: 20px 0 15px 0; font-weight: bold; text-align: center;">'
            '📍 معلومات الموقع التفصيلية'
            '</div>',
            unsafe_allow_html=True
        )
        
        if city_col in asset_data and pd.notna(asset_data[city_col]):
            st.markdown(
                f'<div style="background: linear-gradient(135deg, #3F7CAC, #5BA8D8); color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;">'
                f'<h4 style="margin:0; font-size: 14px;">المدينة</h4>'
                f'<p style="margin:0; font-size: 18px; font-weight: bold;">{asset_data[city_col]}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        st.markdown('<div class="location-grid">', unsafe_allow_html=True)
        
        for col, label, icon in [
            (building_col, "رقم المبنى", "🏢"),
            (floor_col, "رقم الدور", "🏢"), 
            (room_col, "رقم الغرفة/المكتب", "🚪")
        ]:
            if col in asset_data and pd.notna(asset_data[col]):
                value = str(asset_data[col])
            else:
                value = "غير محدد"
            
            st.markdown(
                f'<div class="location-item">'
                f'<h4 style="margin:0; font-size: 14px;">{icon} {label}</h4>'
                f'<p style="margin:0; font-size: 16px; font-weight: bold;">{value}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # أزرار التحكم
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 تقرير HTML", key=f"html_{asset_data.name}"):
                try:
                    single_asset_df = pd.DataFrame([asset_data])
                    html_content = create_html_report(single_asset_df, f"تقرير مفصل للأصل {asset_data.get(unique_asset_col, '')}")
                    st.download_button(
                        "⬇️ تحميل HTML",
                        data=html_content,
                        file_name=f"تقرير_مفصل_{asset_data.get(unique_asset_col, asset_data.name)}.html",
                        mime="text/html",
                        key=f"dl_html_{asset_data.name}"
                    )
                except Exception as e:
                    st.error(f"خطأ في إنشاء التقرير: {e}")
        
        with col2:
            if st.button("📊 تحليل مفصل", key=f"analyze_{asset_data.name}"):
                st.session_state[f'analyze_asset_{asset_data.name}'] = True
        
        with col3:
            if st.button("🖨️ طباعة البطاقة", key=f"print_{asset_data.name}"):
                st.markdown("""
                <script>
                window.print();
                </script>
                """, unsafe_allow_html=True)

# قسم إنشاء التقارير
st.markdown("---")
st.subheader("📄 إنشاء تقارير قابلة للطباعة")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 تقرير شامل لجميع الأصول", use_container_width=True):
        with st.spinner("جاري إنشاء التقرير الشامل..."):
            try:
                html_content = create_html_report(df_filtered, "تقرير شامل لجميع الأصول")
                st.success("✅ تم إنشاء التقرير الشامل بنجاح!")
                st.download_button(
                    "⬇️ تحميل التقرير HTML",
                    data=html_content,
                    file_name="تقرير_الأصول_الشامل.html",
                    mime="text/html",
                    use_container_width=True
                )
                
                # عرض معاينة
                with st.expander("معاينة التقرير"):
                    st.components.v1.html(html_content, height=600, scrolling=True)
                    
            except Exception as e:
                st.error(f"❌ خطأ في إنشاء التقرير: {e}")

with col2:
    if st.button("📊 تقرير إحصائي", use_container_width=True):
        with st.spinner("جاري إنشاء التقرير الإحصائي..."):
            try:
                html_content = create_html_report(df_filtered, "تقرير إحصائي")
                st.success("✅ تم إنشاء التقرير الإحصائي بنجاح!")
                st.download_button(
                    "⬇️ تحميل التقرير الإحصائي",
                    data=html_content,
                    file_name="تقرير_إحصائي_الأصول.html",
                    mime="text/html",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ خطأ في إنشاء التقرير: {e}")

with col3:
    if st.button("💾 تصدير بيانات Excel", use_container_width=True):
        with st.spinner("جاري إنشاء ملف Excel..."):
            try:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df_filtered.to_excel(writer, index=False, sheet_name='الأصول')
                    
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
                st.success("✅ تم إنشاء ملف Excel بنجاح!")
                st.download_button(
                    "⬇️ تحميل Excel",
                    data=excel_buffer,
                    file_name="البيانات_المصفاة.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ خطأ في إنشاء ملف Excel: {e}")

# عرض النتائج
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
        assets_to_display = df_filtered.iloc[start_idx:end_idx]
        
        for idx, asset in assets_to_display.iterrows():
            asset.name = idx
            display_asset_card(asset)

# عرض الجدول التقليدي
if display_mode in ["جدول تقليدي", "كلا الوضعين"]:
    st.markdown("### 📊 عرض جدولي")
    
    if total_assets > 0:
        display_columns = [
            unique_asset_col, tag_col, desc_col, 
            cost_col, nbv_col, city_col,
            building_col, floor_col, room_col
        ]
        
        available_columns = [col for col in display_columns if col in df_filtered.columns]
        
        if available_columns:
            display_df = df_filtered[available_columns].iloc[start_idx:end_idx].copy()
            
            if cost_col in display_df.columns:
                display_df[cost_col] = display_df[cost_col].apply(
                    lambda x: f"{x:,.2f}" if pd.notna(x) and str(x).replace('.','').isdigit() else str(x)
                )
            if nbv_col in display_df.columns:
                display_df[nbv_col] = display_df[nbv_col].apply(
                    lambda x: f"{x:,.2f}" if pd.notna(x) and str(x).replace('.','').isdigit() else str(x)
                )
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 5.1 - تقارير HTML قابلة للطباعة</h3>'
    '<p style="margin:5px 0 0 0;">تقارير متكاملة قابلة للطباعة والتحميل بتنسيق HTML</p>'
    '</div>', 
    unsafe_allow_html=True
)
