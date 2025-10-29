import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
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
    .search-box {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .warning-card {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
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
    st.caption("الإصدار: 6.1 - النظام الذكي المحسن")

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

# تحضير البيانات وتحويل الأنواع
@st.cache_data(show_spinner="جاري تحضير البيانات...")
def process_data(df_raw):
    try:
        df_processed = prepare_dataframe(df_raw)
        
        # تحويل الأعمدة المالية إلى رقمية
        financial_columns = ['Cost', 'Net Book Value', 'Accumulated Depreciation', 'Residual Value']
        for col in financial_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
        
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

# الحصول على أعمدة البحث مع القيم الافتراضية
unique_asset_col = colmap.get("Asset Unique No") or "Unique Asset Number in the entity"
tag_col = colmap.get("Tag Number") or "Tag number"
desc_col = colmap.get("Description") or "Asset Description"
cost_col = colmap.get("Cost") or "Cost"
nbv_col = colmap.get("Net Book Value") or "Net Book Value"
city_col = colmap.get("City") or "City"
building_col = colmap.get("Building") or "Building Numbe"
floor_col = colmap.get("Floor") or "Floor"
room_col = colmap.get("Room/Office") or "Room/Office"

# 🔧 دالة لتحويل الأعمدة إلى رقمية
def convert_to_numeric(df, column_name):
    """تحويل عمود إلى قيم رقمية مع معالجة الأخطاء"""
    if column_name not in df.columns:
        return df, False
    
    original_dtype = df[column_name].dtype
    if np.issubdtype(original_dtype, np.number):
        return df, True
    
    # محاولة التحويل
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    successful_conversion = df[column_name].notna().any()
    
    return df, successful_conversion

# 🔍 البحث الذكي المتقدم
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

# 📊 لوحة التحكم التفاعلية (Dashboard)
def create_dashboard(df):
    """إنشاء لوحة تحكم تفاعلية مع مؤشرات الأداء"""
    
    st.markdown("---")
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>📊 لوحة التحكم الشاملة</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # تحويل الأعمدة المالية إلى رقمية
    df_processed = df.copy()
    cost_converted = False
    nbv_converted = False
    
    if cost_col in df_processed.columns:
        df_processed, cost_converted = convert_to_numeric(df_processed, cost_col)
    
    if nbv_col in df_processed.columns:
        df_processed, nbv_converted = convert_to_numeric(df_processed, nbv_col)
    
    # حساب المؤشرات الأساسية
    total_assets = len(df_processed)
    
    # حساب القيم المالية مع التحقق من التحويل
    if cost_converted:
        total_cost = df_processed[cost_col].sum()
        avg_cost = total_cost / total_assets if total_assets > 0 else 0
    else:
        total_cost = 0
        avg_cost = 0
    
    if nbv_converted:
        total_nbv = df_processed[nbv_col].sum()
    else:
        total_nbv = 0
    
    # حساب معدل الاستهلاك
    if cost_converted and nbv_converted and total_cost > 0:
        total_depreciation = (df_processed[cost_col] - df_processed[nbv_col]).sum()
        depreciation_rate = (total_depreciation / total_cost * 100)
    else:
        depreciation_rate = 0
    
    # عرض تحذيرات إذا كانت هناك مشاكل في البيانات
    if not cost_converted or not nbv_converted:
        st.markdown('<div class="warning-card">', unsafe_allow_html=True)
        st.warning("⚠️ بعض البيانات المالية تحتوي على قيم غير رقمية وقد لا تظهر جميع التحليلات")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # مؤشرات الأداء الرئيسية
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>إجمالي الأصول</h3>
            <p style='margin:0; font-size: 24px; font-weight: bold; color: #333;'>{total_assets:,}</p>
            <p style='margin:0; font-size: 12px; color: #666;'>الأصول المسجلة</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>القيمة الإجمالية</h3>
            <p style='margin:0; font-size: 20px; font-weight: bold; color: #333;'>{total_cost:,.0f} ريال</p>
            <p style='margin:0; font-size: 12px; color: #666;'>إجمالي التكلفة</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style='margin:0; color: #1f77b4;'>صافي القيمة</h3>
            <p style='margin:0; font-size: 20px; font-weight: bold; color: #333;'>{total_nbv:,.0f} ريال</p>
            <p style='margin:0; font-size: 12px; color: #666;'>القيمة الدفترية</p>
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
        if city_col in df_processed.columns:
            city_data = df_processed[city_col].value_counts().head(8)
            
            if not city_data.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                colors = plt.cm.Set3(np.linspace(0, 1, len(city_data)))
                wedges, texts, autotexts = ax.pie(
                    city_data.values, 
                    labels=city_data.index,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors
                )
                
                # تحسين مظهر النصوص
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax.set_title('توزيع الأصول حسب المدينة', fontsize=14, fontweight='bold')
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("لا توجد بيانات كافية لعرض التوزيع الجغرافي")
    
    with col2:
        # توزيع القيم إذا كانت البيانات رقمية
        if cost_converted:
            fig, ax = plt.subplots(figsize=(10, 6))
            valid_costs = df_processed[cost_col].dropna()
            if not valid_costs.empty:
                valid_costs.hist(bins=20, ax=ax, color='skyblue', alpha=0.7, edgecolor='black')
                ax.set_title('توزيع قيم الأصول', fontsize=14, fontweight='bold')
                ax.set_xlabel('التكلفة (ريال)')
                ax.set_ylabel('عدد الأصول')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.info("لا توجد بيانات مالية صالحة للعرض")
        else:
            st.info("بيانات التكلفة غير متاحة للتحليل")
    
    # تحليل القيمة المتبقية إذا كانت البيانات متاحة
    if cost_converted and nbv_converted:
        st.markdown("---")
        st.subheader("💰 تحليل القيمة المتبقية")
        
        # حساب القيمة المتبقية مع معالجة الأخطاء
        valid_financial_data = df_processed.dropna(subset=[cost_col, nbv_col])
        valid_financial_data = valid_financial_data[valid_financial_data[cost_col] > 0]
        
        if not valid_financial_data.empty:
            valid_financial_data = valid_financial_data.copy()
            valid_financial_data['Remaining Value %'] = (
                valid_financial_data[nbv_col] / valid_financial_data[cost_col] * 100
            ).round(1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # توزيع القيمة المتبقية
                fig, ax = plt.subplots(figsize=(10, 6))
                valid_financial_data['Remaining Value %'].hist(
                    bins=20, ax=ax, color='lightgreen', alpha=0.7, edgecolor='black'
                )
                ax.set_title('توزيع نسبة القيمة المتبقية', fontsize=14, fontweight='bold')
                ax.set_xlabel('نسبة القيمة المتبقية (%)')
                ax.set_ylabel('عدد الأصول')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
            
            with col2:
                # أعلى 10 أصول قيمة
                top_assets = valid_financial_data.nlargest(10, cost_col)[
                    [unique_asset_col, cost_col, nbv_col, 'Remaining Value %']
                ]
                
                # تنسيق الأرقام للعرض
                display_df = top_assets.copy()
                display_df[cost_col] = display_df[cost_col].apply(lambda x: f"{x:,.0f}")
                display_df[nbv_col] = display_df[nbv_col].apply(lambda x: f"{x:,.0f}")
                display_df['Remaining Value %'] = display_df['Remaining Value %'].apply(lambda x: f"{x}%")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )

# 📈 تحليل القيمة والاستهلاك
def depreciation_analysis(df):
    """تحليل متقدم للقيمة والاستهلاك"""
    
    st.markdown("---")
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>📊 تحليل القيمة والاستهلاك</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # تحويل الأعمدة المالية
    df_processed = df.copy()
    cost_converted = False
    nbv_converted = False
    
    if cost_col in df_processed.columns:
        df_processed, cost_converted = convert_to_numeric(df_processed, cost_col)
    
    if nbv_col in df_processed.columns:
        df_processed, nbv_converted = convert_to_numeric(df_processed, nbv_col)
    
    if not cost_converted or not nbv_converted:
        st.error("❌ لا توجد بيانات مالية صالحة للتحليل")
        return
    
    # حساب معدلات الاستهلاك
    valid_data = df_processed.dropna(subset=[cost_col, nbv_col])
    valid_data = valid_data[valid_data[cost_col] > 0]
    
    if valid_data.empty:
        st.warning("⚠️ لا توجد بيانات مالية كافية للتحليل")
        return
    
    df_analysis = valid_data.copy()
    df_analysis['Accumulated Depreciation'] = df_analysis[cost_col] - df_analysis[nbv_col]
    df_analysis['Depreciation Rate %'] = (
        df_analysis['Accumulated Depreciation'] / df_analysis[cost_col] * 100
    ).round(1)
    df_analysis['Remaining Value %'] = (
        df_analysis[nbv_col] / df_analysis[cost_col] * 100
    ).round(1)
    
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
        fig, ax = plt.subplots(figsize=(10, 6))
        df_analysis['Depreciation Rate %'].hist(bins=20, ax=ax, color='skyblue', alpha=0.7, edgecolor='black')
        ax.set_title('توزيع معدلات الاستهلاك', fontsize=14, fontweight='bold')
        ax.set_xlabel('معدل الاستهلاك (%)')
        ax.set_ylabel('عدد الأصول')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        # العلاقة بين التكلفة ومعدل الاستهلاك
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(
            df_analysis[cost_col], 
            df_analysis['Depreciation Rate %'], 
            alpha=0.6, 
            c=df_analysis['Depreciation Rate %'], 
            cmap='viridis'
        )
        ax.set_title('العلاقة بين التكلفة ومعدل الاستهلاك', fontsize=14, fontweight='bold')
        ax.set_xlabel('التكلفة (ريال)')
        ax.set_ylabel('معدل الاستهلاك (%)')
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax)
        plt.tight_layout()
        st.pyplot(fig)

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
    st.info("👆 استخدم البحث أعلاه للعثور على الأصول المطلوبة")
    st.info("🚀 انتقل إلى وضع 'جميع الوظائف' للحصول على تجربة كاملة")

else:  # جميع الوظائف
    create_dashboard(df_filtered)
    depreciation_analysis(df_filtered)

# عرض إحصائيات سريعة
total_filtered = len(df_filtered)
if total_filtered > 0:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 نتائج البحث")
    st.sidebar.metric("عدد الأصول المطابقة", total_filtered)

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 6.1 - النظام الذكي المحسن</h3>'
    '<p style="margin:5px 0 0 0;">معالجة ذكية للبيانات المالية</p>'
    '</div>', 
    unsafe_allow_html=True
)
