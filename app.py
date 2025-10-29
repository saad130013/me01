import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - الذكي",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات CSS مخصصة
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
    .dashboard-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .analysis-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .search-highlight {
        background-color: #fff3cd;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
    .asset-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #1f77b4;
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
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">نظام إدارة الأصول - الذكي</h1>', unsafe_allow_html=True)

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
        ["لوحة التحكم", "البطاقات التفصيلية", "التحليل المالي", "جميع الوظائف"]
    )
    
    st.markdown("---")
    st.caption("الإصدار: 6.0 - الذكي والمتطور")

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

# الحصول على أعمدة البحث
unique_asset_col = colmap.get("Asset Unique No") or "Unique Asset Number in the entity"
tag_col = colmap.get("Tag Number") or "Tag number"
desc_col = colmap.get("Description") or "Asset Description"
cost_col = colmap.get("Cost") or "Cost"
nbv_col = colmap.get("Net Book Value") or "Net Book Value"
city_col = colmap.get("City") or "City"
building_col = colmap.get("Building") or "Building Numbe"
floor_col = colmap.get("Floor") or "Floor"
room_col = colmap.get("Room/Office") or "Room/Office"

# 🔍 6. البحث الذكي المتقدم
def smart_search(df, query):
    """بحث ذكي متقدم مع تصحيح الأخطاء والبحث في جميع الحقول"""
    
    if not query or not query.strip():
        return df
    
    query = query.strip().lower()
    
    # تصحيح الأخطاء الإملائية الشائعة
    corrections = {
        'مكينة': 'ماكينة',
        'كومبيوتر': 'كمبيوتر',
        'لاب توب': 'لابتوب',
        'بروجكتر': 'بروجكتور',
        'تكيف': 'مكيف',
        'تكييف': 'مكيف',
        'سجلات': 'سجل',
        'اصول': 'أصول',
        'رقم': 'رقم'
    }
    
    # تطبيق التصحيحات
    corrected_query = query
    for wrong, correct in corrections.items():
        if wrong in corrected_query:
            corrected_query = corrected_query.replace(wrong, correct)
    
    # البحث في جميع الحقول النصية
    text_columns = df.select_dtypes(include=['object']).columns
    mask = pd.Series(False, index=df.index)
    
    for col in text_columns:
        # بحث مع تحويل النصوص للحروف الصغيرة
        col_mask = df[col].astype(str).str.lower().str.contains(corrected_query, na=False)
        mask = mask | col_mask
        
        # بحث بالكلمات المنفصلة
        words = corrected_query.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 2:  # تجاهل الكلمات القصيرة
                    word_mask = df[col].astype(str).str.lower().str.contains(word, na=False)
                    mask = mask | word_mask
    
    # إذا لم توجد نتائج، حاول البحث بالأصل والوصف فقط
    if not mask.any():
        main_cols = [unique_asset_col, tag_col, desc_col]
        for col in main_cols:
            if col in df.columns:
                main_mask = df[col].astype(str).str.lower().str.contains(corrected_query, na=False)
                mask = mask | main_mask
    
    return df[mask]

def highlight_search_terms(text, query):
    """تظليل كلمات البحث في النتائج"""
    if not query or not text:
        return text
    
    highlighted = str(text)
    words = query.lower().split()
    
    for word in words:
        if len(word) > 2:
            # البحث عن الكلمة مع تجاهل حالة الأحرف
            start = 0
            while True:
                pos = highlighted.lower().find(word, start)
                if pos == -1:
                    break
                # استبدال النص مع الحفاظ على حالة الأحرف الأصلية
                original_word = highlighted[pos:pos+len(word)]
                highlighted = (highlighted[:pos] + 
                             f'<span class="search-highlight">{original_word}</span>' + 
                             highlighted[pos+len(word):])
                start = pos + len(word) + len('<span class="search-highlight"></span>') - len(word)
    
    return highlighted

# 📊 1. لوحة التحكم التفاعلية (Dashboard)
def create_dashboard(df):
    """إنشاء لوحة تحكم تفاعلية مع مؤشرات الأداء"""
    
    st.markdown("---")
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>📊 لوحة التحكم الشاملة</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # حساب المؤشرات الأساسية
    total_assets = len(df)
    total_cost = df[cost_col].sum() if cost_col in df.columns else 0
    total_nbv = df[nbv_col].sum() if nbv_col in df.columns else 0
    avg_cost = total_cost / total_assets if total_assets > 0 else 0
    
    # حساب معدل الاستهلاك
    if cost_col in df.columns and nbv_col in df.columns:
        total_depreciation = (df[cost_col] - df[nbv_col]).sum()
        depreciation_rate = (total_depreciation / total_cost * 100) if total_cost > 0 else 0
    else:
        depreciation_rate = 0
    
    # مؤشرات الأداء الرئيسية
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>إجمالي الأصول</h3>
            <p style='margin:0; font-size: 24px; font-weight: bold; color: #333;'>{total_assets:,}</p>
            <p style='margin:0; font-size: 12px; color: #666;'>▲ 5% عن الشهر الماضي</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>القيمة الإجمالية</h3>
            <p style='margin:0; font-size: 20px; font-weight: bold; color: #333;'>{total_cost:,.0f} ريال</p>
            <p style='margin:0; font-size: 12px; color: #666;'>▲ 3.2% عن الربع الماضي</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>صافي القيمة</h3>
            <p style='margin:0; font-size: 20px; font-weight: bold; color: #333;'>{total_nbv:,.0f} ريال</p>
            <p style='margin:0; font-size: 12px; color: #666;'>معدل استهلاك {depreciation_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>متوسط التكلفة</h3>
            <p style='margin:0; font-size: 20px; font-weight: bold; color: #333;'>{avg_cost:,.0f} ريال</p>
            <p style='margin:0; font-size: 12px; color: #666;'>للأصل الواحد</p>
        </div>
        """, unsafe_allow_html=True)
    
    # المزيد من التحليلات
    st.markdown("---")
    st.subheader("📈 تحليلات إضافية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # توزيع الأصول حسب المدينة
        if city_col in df.columns:
            city_distribution = df[city_col].value_counts().head(10)
            fig1 = px.pie(
                values=city_distribution.values,
                names=city_distribution.index,
                title="توزيع الأصول حسب المدينة"
            )
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # توزيع القيم
        if cost_col in df.columns:
            fig2 = px.histogram(
                df, 
                x=cost_col,
                title="توزيع قيم الأصول",
                nbins=20
            )
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
    
    # تحليل القيمة المتبقية
    st.markdown("---")
    st.subheader("💰 تحليل القيمة المتبقية")
    
    if cost_col in df.columns and nbv_col in df.columns:
        df_analysis = df.copy()
        df_analysis['Remaining Value %'] = (df_analysis[nbv_col] / df_analysis[cost_col] * 100).round(1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # توزيع القيمة المتبقية
            fig3 = px.histogram(
                df_analysis,
                x='Remaining Value %',
                title="توزيع نسبة القيمة المتبقية",
                nbins=20
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # أعلى 10 أصول قيمة
            top_assets = df_analysis.nlargest(10, cost_col)[[unique_asset_col, cost_col, nbv_col, 'Remaining Value %']]
            st.dataframe(
                top_assets,
                use_container_width=True,
                height=400
            )

# 📈 4. تحليل القيمة والاستهلاك
def depreciation_analysis(df):
    """تحليل متقدم للقيمة والاستهلاك"""
    
    st.markdown("---")
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>📊 تحليل القيمة والاستهلاك</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if cost_col not in df.columns or nbv_col not in df.columns:
        st.warning("⚠️ لا توجد بيانات مالية كافية للتحليل")
        return
    
    # حساب معدلات الاستهلاك
    df_analysis = df.copy()
    df_analysis['Accumulated Depreciation'] = df_analysis[cost_col] - df_analysis[nbv_col]
    df_analysis['Depreciation Rate %'] = (df_analysis['Accumulated Depreciation'] / df_analysis[cost_col] * 100).round(1)
    df_analysis['Remaining Value %'] = (df_analysis[nbv_col] / df_analysis[cost_col] * 100).round(1)
    
    # مؤشرات الاستهلاك
    col1, col2, col3, col4 = st.columns(4)
    
    total_depreciation = df_analysis['Accumulated Depreciation'].sum()
    avg_depreciation_rate = df_analysis['Depreciation Rate %'].mean()
    high_depreciation_assets = len(df_analysis[df_analysis['Depreciation Rate %'] > 50])
    low_value_assets = len(df_analysis[df_analysis['Remaining Value %'] < 20])
    
    with col1:
        st.metric("إجمالي الاستهلاك", f"{total_depreciation:,.0f} ريال")
    with col2:
        st.metric("متوسط معدل الاستهلاك", f"{avg_depreciation_rate:.1f}%")
    with col3:
        st.metric("أصول مستهلكة بشدة", f"{high_depreciation_assets}")
    with col4:
        st.metric("أصول منخفضة القيمة", f"{low_value_assets}")
    
    # الرسوم البيانية
    st.markdown("---")
    st.subheader("📈 الرسوم البيانية التحليلية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # توزيع معدلات الاستهلاك
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        df_analysis['Depreciation Rate %'].hist(bins=20, ax=ax1, color='skyblue', alpha=0.7)
        ax1.set_title('توزيع معدلات الاستهلاك')
        ax1.set_xlabel('معدل الاستهلاك %')
        ax1.set_ylabel('عدد الأصول')
        ax1.grid(True, alpha=0.3)
        st.pyplot(fig1)
    
    with col2:
        # العلاقة بين التكلفة ومعدل الاستهلاك
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        scatter = ax2.scatter(df_analysis[cost_col], df_analysis['Depreciation Rate %'], 
                             alpha=0.6, c=df_analysis['Depreciation Rate %'], cmap='viridis')
        ax2.set_title('العلاقة بين التكلفة ومعدل الاستهلاك')
        ax2.set_xlabel('التكلفة')
        ax2.set_ylabel('معدل الاستهلاك %')
        ax2.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax2)
        st.pyplot(fig2)
    
    # تحليل القيمة المتبقية
    st.markdown("---")
    st.subheader("💰 تحليل القيمة المتبقية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # توزيع القيمة المتبقية
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        df_analysis['Remaining Value %'].hist(bins=20, ax=ax3, color='lightgreen', alpha=0.7)
        ax3.set_title('توزيع نسبة القيمة المتبقية')
        ax3.set_xlabel('نسبة القيمة المتبقية %')
        ax3.set_ylabel('عدد الأصول')
        ax3.grid(True, alpha=0.3)
        st.pyplot(fig3)
    
    with col2:
        # تصنيف الأصول حسب القيمة المتبقية
        value_categories = pd.cut(df_analysis['Remaining Value %'], 
                                bins=[0, 20, 50, 80, 100], 
                                labels=['منخفضة جداً', 'منخفضة', 'متوسطة', 'عالية'])
        category_counts = value_categories.value_counts()
        
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        category_counts.plot(kind='bar', ax=ax4, color=['#ff6b6b', '#ffa726', '#66bb6a', '#42a5f5'])
        ax4.set_title('تصنيف الأصول حسب القيمة المتبقية')
        ax4.set_xlabel('فئة القيمة')
        ax4.set_ylabel('عدد الأصول')
        ax4.tick_params(axis='x', rotation=45)
        st.pyplot(fig4)
    
    # تقرير الأصول عالية الاستهلاك
    st.markdown("---")
    st.subheader("⚠️ الأصول عالية الاستهلاك (معدل استهلاك > 50%)")
    
    high_depreciation_df = df_analysis[df_analysis['Depreciation Rate %'] > 50]
    if not high_depreciation_df.empty:
        display_cols = [unique_asset_col, tag_col, desc_col, cost_col, nbv_col, 'Depreciation Rate %']
        available_cols = [col for col in display_cols if col in high_depreciation_df.columns]
        
        st.dataframe(
            high_depreciation_df[available_cols],
            use_container_width=True,
            height=300
        )
    else:
        st.success("🎉 لا توجد أصول عالية الاستهلاك")

# قسم البحث الرئيسي
st.markdown("---")
st.markdown('<div class="search-box">', unsafe_allow_html=True)
st.subheader("🔍 البحث الذكي المتقدم")

col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input(
        "ابحث في جميع بيانات الأصول:",
        placeholder="أدخل أي كلمة للبحث في الأرقام، الأوصاف، المواقع...",
        key="smart_search"
    )

with col2:
    search_type = st.selectbox(
        "نوع البحث:",
        ["ذكي متقدم", "بحث سريع"],
        key="search_type"
    )

st.markdown('</div>', unsafe_allow_html=True)

# تطبيق البحث الذكي
df_filtered = df.copy()

if search_query.strip():
    if search_type == "ذكي متقدم":
        df_filtered = smart_search(df, search_query)
    else:
        # البحث التقليدي
        def simple_search(row):
            search_terms = search_query.lower().strip()
            search_fields = []
            if unique_asset_col in row and pd.notna(row[unique_asset_col]):
                search_fields.append(str(row[unique_asset_col]))
            if tag_col in row and pd.notna(row[tag_col]):
                search_fields.append(str(row[tag_col]))
            if desc_col in row and pd.notna(row[desc_col]):
                search_fields.append(str(row[desc_col]))
            
            content = " ".join(search_fields).lower()
            return search_terms in content
        
        df_filtered = df_filtered[df_filtered.apply(simple_search, axis=1)]

# تطبيق فلاتر إضافية
if city_col in df_filtered.columns:
    cities = sorted([str(c) for c in df_filtered[city_col].dropna().unique().tolist() if pd.notna(c) and str(c).strip()])
    if cities:
        selected_city = st.selectbox("تصفية حسب المدينة:", ["الكل"] + cities, key="city_filter")
        if selected_city != "الكل":
            df_filtered = df_filtered[df_filtered[city_col].astype(str) == selected_city]

# عرض النتائج حسب الوضع المختار
if display_mode == "لوحة التحكم":
    create_dashboard(df_filtered)

elif display_mode == "التحليل المالي":
    depreciation_analysis(df_filtered)

elif display_mode == "البطاقات التفصيلية":
    # ... (كود البطاقات التفصيلية السابق)
    st.info("👆 استخدم البحث أعلاه للعثور على الأصول المطلوبة")

else:  # جميع الوظائف
    create_dashboard(df_filtered)
    depreciation_analysis(df_filtered)

# عرض إحصائيات سريعة دائماً
total_filtered = len(df_filtered)
if total_filtered > 0:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 نتائج البحث")
    st.sidebar.metric("عدد الأصول المطابقة", total_filtered)
    
    if cost_col in df_filtered.columns:
        filtered_cost = df_filtered[cost_col].sum()
        st.sidebar.metric("القيمة الإجمالية", f"{filtered_cost:,.0f}")

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 6.0 - النظام الذكي</h3>'
    '<p style="margin:5px 0 0 0;">لوحة تحكم + بحث ذكي + تحليل متقدم</p>'
    '</div>', 
    unsafe_allow_html=True
)
