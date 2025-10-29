import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import arabic_reshaper
from bidi.algorithm import get_display
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - تقارير PDF",
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
    .building-value {
        background: linear-gradient(135deg, #11998e, #38ef7d);
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
    .pdf-button {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 12px 24px;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        margin: 5px;
    }
    .pdf-button:hover {
        background: linear-gradient(135deg, #ee5a24, #ff6b6b);
    }
    @media (max-width: 768px) {
        .quick-stats {
            grid-template-columns: 1fr;
        }
        .location-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">نظام إدارة الأصول - تقارير PDF شاملة</h1>', unsafe_allow_html=True)

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
    st.header("📊 خيارات PDF")
    pdf_report_type = st.selectbox(
        "نوع التقرير:",
        ["تقرير مفصل لكل أصل", "تقرير شامل لجميع الأصول", "تقرير إحصائي"]
    )
    
    st.caption("الإصدار: 5.0 - تقارير PDF شاملة")

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

# دالة لإنشاء PDF شامل
def create_comprehensive_pdf(assets_data, report_type="تقرير شامل لجميع الأصول"):
    """إنشاء تقرير PDF شامل"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # إضافة نمط للنص العربي
    arabic_style = ParagraphStyle(
        'ArabicStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        alignment=TA_RIGHT,
        rightIndent=0,
        wordWrap='RTL'
    )
    
    # عنوان التقرير
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    title = Paragraph(f"تقرير شامل للأصول - {report_type}", title_style)
    elements.append(title)
    
    # معلومات التقرير
    info_text = f"""
    <b>تاريخ التقرير:</b> {pd.Timestamp.now().strftime('%Y-%m-%d')}<br/>
    <b>عدد الأصول:</b> {len(assets_data):,}<br/>
    <b>إجمالي التكلفة:</b> {total_cost:,.2f}<br/>
    <b>صافي القيمة الدفترية:</b> {total_nbv:,.2f}<br/>
    """
    
    info_paragraph = Paragraph(info_text, arabic_style)
    elements.append(info_paragraph)
    elements.append(Spacer(1, 20))
    
    if report_type == "تقرير إحصائي":
        # إحصائيات حسب المدينة
        if city_col in assets_data.columns:
            city_stats = assets_data.groupby(city_col).agg({
                cost_col: 'sum',
                nbv_col: 'sum',
                unique_asset_col: 'count'
            }).reset_index()
            
            city_stats.columns = ['المدينة', 'إجمالي التكلفة', 'صافي القيمة', 'عدد الأصول']
            
            # إنشاء جدول الإحصائيات
            data = [['المدينة', 'عدد الأصول', 'إجمالي التكلفة', 'صافي القيمة']]
            
            for _, row in city_stats.iterrows():
                data.append([
                    str(row['المدينة']),
                    str(row['عدد الأصول']),
                    f"{row['إجمالي التكلفة']:,.2f}",
                    f"{row['صافي القيمة']:,.2f}"
                ])
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
    else:
        # بيانات مفصلة لكل أصل
        display_columns = [
            unique_asset_col, tag_col, desc_col, 
            cost_col, nbv_col, city_col,
            building_col, floor_col, room_col
        ]
        
        # تصفية الأعمدة الموجودة فقط
        available_columns = [col for col in display_columns if col in assets_data.columns]
        
        if available_columns:
            # عناوين الأعمدة
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
            
            data = [[headers.get(col, col) for col in available_columns]]
            
            for _, asset in assets_data.iterrows():
                row_data = []
                for col in available_columns:
                    value = asset[col]
                    if pd.isna(value):
                        row_data.append("---")
                    elif col in [cost_col, nbv_col]:
                        try:
                            row_data.append(f"{float(value):,.2f}")
                        except:
                            row_data.append(str(value))
                    else:
                        # تقصير الوصف الطويل
                        if col == desc_col and len(str(value)) > 50:
                            row_data.append(str(value)[:50] + "...")
                        else:
                            row_data.append(str(value))
                data.append(row_data)
            
            # إنشاء الجدول
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(table)
    
    # تذييل الصفحة
    elements.append(Spacer(1, 20))
    footer = Paragraph(f"تم إنشاء التقرير بواسطة نظام إدارة الأصول - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", arabic_style)
    elements.append(footer)
    
    # بناء PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# دالة لإنشاء PDF مفصل لأصل واحد
def create_single_asset_pdf(asset_data):
    """إنشاء PDF مفصل لأصل واحد"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # إضافة نمط للنص العربي
    arabic_style = ParagraphStyle(
        'ArabicStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        alignment=TA_RIGHT,
        rightIndent=0,
        wordWrap='RTL'
    )
    
    # عنوان التقرير
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    asset_id = asset_data[unique_asset_col] if unique_asset_col in asset_data and pd.notna(asset_data[unique_asset_col]) else "غير محدد"
    title = Paragraph(f"تقرير مفصل للأصل - {asset_id}", title_style)
    elements.append(title)
    
    # معلومات الأساسية
    elements.append(Paragraph("<b>المعلومات الأساسية:</b>", arabic_style))
    
    basic_info = [
        ("رقم الأصل الفريد", unique_asset_col),
        ("رقم الوسم", tag_col),
        ("وصف الأصل", desc_col)
    ]
    
    basic_data = [['المعلومة', 'القيمة']]
    for label, col in basic_info:
        if col in asset_data and pd.notna(asset_data[col]):
            basic_data.append([label, str(asset_data[col])])
    
    basic_table = Table(basic_data)
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(basic_table)
    elements.append(Spacer(1, 20))
    
    # المعلومات المالية
    elements.append(Paragraph("<b>المعلومات المالية:</b>", arabic_style))
    
    financial_data = [['البند', 'القيمة']]
    if cost_col in asset_data and pd.notna(asset_data[cost_col]):
        try:
            financial_data.append(['التكلفة', f"{float(asset_data[cost_col]):,.2f}"])
        except:
            financial_data.append(['التكلفة', str(asset_data[cost_col])])
    
    if nbv_col in asset_data and pd.notna(asset_data[nbv_col]):
        try:
            financial_data.append(['صافي القيمة الدفترية', f"{float(asset_data[nbv_col]):,.2f}"])
        except:
            financial_data.append(['صافي القيمة الدفترية', str(asset_data[nbv_col])])
    
    financial_table = Table(financial_data)
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F18F01')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(financial_table)
    elements.append(Spacer(1, 20))
    
    # معلومات الموقع
    elements.append(Paragraph("<b>معلومات الموقع:</b>", arabic_style))
    
    location_data = [['نوع الموقع', 'القيمة']]
    location_fields = [
        ("المدينة", city_col),
        ("رقم المبنى", building_col),
        ("الدور", floor_col),
        ("الغرفة/المكتب", room_col)
    ]
    
    for label, col in location_fields:
        if col in asset_data and pd.notna(asset_data[col]):
            location_data.append([label, str(asset_data[col])])
    
    location_table = Table(location_data)
    location_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3F7CAC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(location_table)
    
    # بناء PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

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
        
        # ... (بقية كود البطاقة كما هو سابقاً)
        # [يتم حذف جزء من الكود للإيجاز - الكود السابق للبطاقة يبقى كما هو]
        
        # أزرار PDF محسنة
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 إنشاء PDF مفصل", key=f"pdf_single_{asset_data.name}"):
                try:
                    pdf_buffer = create_single_asset_pdf(asset_data)
                    asset_id = asset_data[unique_asset_col] if unique_asset_col in asset_data and pd.notna(asset_data[unique_asset_col]) else f"asset_{asset_data.name}"
                    st.download_button(
                        "⬇️ تحميل PDF مفصل",
                        data=pdf_buffer,
                        file_name=f"تقرير_مفصل_{asset_id}.pdf",
                        mime="application/pdf",
                        key=f"dl_single_{asset_data.name}"
                    )
                except Exception as e:
                    st.error(f"خطأ في إنشاء PDF: {e}")
        
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

# قسم إنشاء التقارير PDF
st.markdown("---")
st.subheader("📄 إنشاء تقارير PDF")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 تقرير شامل لجميع الأصول", use_container_width=True):
        with st.spinner("جاري إنشاء التقرير الشامل..."):
            try:
                pdf_buffer = create_comprehensive_pdf(df_filtered, "تقرير شامل لجميع الأصول")
                st.success("✅ تم إنشاء التقرير الشامل بنجاح!")
                st.download_button(
                    "⬇️ تحميل التقرير الشامل",
                    data=pdf_buffer,
                    file_name="تقرير_الأصول_الشامل.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ خطأ في إنشاء التقرير: {e}")

with col2:
    if st.button("📊 تقرير إحصائي", use_container_width=True):
        with st.spinner("جاري إنشاء التقرير الإحصائي..."):
            try:
                pdf_buffer = create_comprehensive_pdf(df_filtered, "تقرير إحصائي")
                st.success("✅ تم إنشاء التقرير الإحصائي بنجاح!")
                st.download_button(
                    "⬇️ تحميل التقرير الإحصائي",
                    data=pdf_buffer,
                    file_name="تقرير_إحصائي_الأصول.pdf",
                    mime="application/pdf",
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

# ... (بقية الكود يبقى كما هو)

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 5.0 - تقارير PDF شاملة</h3>'
    '<p style="margin:5px 0 0 0;">تقارير PDF متكاملة قابلة للطباعة والتحميل</p>'
    '</div>', 
    unsafe_allow_html=True
)
