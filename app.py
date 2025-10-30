import io
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import re
import json
from utils_pdf import make_asset_pdf
from utils_prepare import prepare_dataframe, guess_columns, parse_coordinates

# إعداد الصفحة
st.set_page_config(
    page_title="نظام إدارة الأصول - المساعد الذكي",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تنسيقات CSS مخصصة للمساعد الذكي
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
    .ai-assistant {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
    .user-message {
        background: #e3f2fd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-right: 4px solid #2196f3;
    }
    .ai-response {
        background: #f3e5f5;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-right: 4px solid #9c27b0;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 10px;
    }
    .metric-highlight {
        background: #ffeb3b;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
        color: #333;
    }
    .analysis-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🤖 المساعد الذكي لإدارة الأصول</h1>', unsafe_allow_html=True)

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
        ["المساعد الذكي", "لوحة التحكم", "التحليل المالي", "جميع الوظائف"]
    )
    
    st.markdown("---")
    st.caption("الإصدار: 7.0 - المساعد الذكي المتكامل")

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
    
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    successful_conversion = df[column_name].notna().any()
    
    return df, successful_conversion

# 🤖 نظام الذكاء الاصطناعي للمساعد
class AssetAIAssistant:
    def __init__(self, df):
        self.df = df
        self.setup_columns()
        self.prepare_data()
        
    def setup_columns(self):
        """إعداد الأعمدة المستخدمة في التحليل"""
        self.unique_asset_col = unique_asset_col
        self.tag_col = tag_col
        self.desc_col = desc_col
        self.cost_col = cost_col
        self.nbv_col = nbv_col
        self.city_col = city_col
        self.building_col = building_col
        
    def prepare_data(self):
        """تحضير البيانات للتحليل"""
        self.df_processed = self.df.copy()
        
        # تحويل الأعمدة المالية
        if self.cost_col in self.df_processed.columns:
            self.df_processed, self.cost_converted = convert_to_numeric(self.df_processed, self.cost_col)
        if self.nbv_col in self.df_processed.columns:
            self.df_processed, self.nbv_converted = convert_to_numeric(self.df_processed, self.nbv_col)
        
        # حساب الإحصائيات الأساسية
        self.total_assets = len(self.df_processed)
        self.total_cost = self.df_processed[self.cost_col].sum() if self.cost_converted else 0
        self.total_nbv = self.df_processed[self.nbv_col].sum() if self.nbv_converted else 0
        
    def analyze_question(self, question):
        """تحليل السؤال وتحديد نوعه"""
        question = question.lower().strip()
        
        # أنماط الأسئلة
        patterns = {
            'count': r'(كم|عدد|كم عدد|ما عدد|كم يوجد|كم لدينا)',
            'cost': r'(تكلفة|سعر|قيمة|ثمن|مبلغ|التكلفة|القيمة)',
            'location': r'(أين|مكان|موقع|في أي|مكان وجود|أين يوجد)',
            'search': r'(ابحث|عرض|أرني|اظهر|جد|ابحث عن|عرض لي)',
            'summary': r'(ملخص|إحصائيات|نظرة|عرض عام|معلومات عامة)',
            'depreciation': r'(استهلاك|إهلاك|مستهلَك|قيمة متبقية|صافي قيمة)',
            'city': r'(مدينة|منطقة|موقع جغرافي|في الرياض|في جدة)',
            'top': r'(أعلى|أكبر|أغلى|أعلى قيمة|أكبر تكلفة)'
        }
        
        question_type = 'general'
        for q_type, pattern in patterns.items():
            if re.search(pattern, question):
                question_type = q_type
                break
                
        return question_type
    
    def generate_response(self, question):
        """توليد رد بناءً على نوع السؤال"""
        question_type = self.analyze_question(question)
        
        if question_type == 'count':
            return self.handle_count_questions(question)
        elif question_type == 'cost':
            return self.handle_cost_questions(question)
        elif question_type == 'location':
            return self.handle_location_questions(question)
        elif question_type == 'search':
            return self.handle_search_questions(question)
        elif question_type == 'summary':
            return self.handle_summary_questions(question)
        elif question_type == 'depreciation':
            return self.handle_depreciation_questions(question)
        elif question_type == 'city':
            return self.handle_city_questions(question)
        elif question_type == 'top':
            return self.handle_top_questions(question)
        else:
            return self.handle_general_questions(question)
    
    def handle_count_questions(self, question):
        """معالجة أسئلة العد والإحصاء"""
        if 'أصل' in question or 'أصول' in question:
            response = f"إجمالي عدد الأصول في النظام: **{self.total_assets:,}** أصل"
            
            if self.city_col in self.df_processed.columns:
                city_counts = self.df_processed[self.city_col].value_counts().head(5)
                if not city_counts.empty:
                    response += "\n\n**التوزيع حسب المدن:**"
                    for city, count in city_counts.items():
                        response += f"\n• {city}: {count:,} أصل"
            
            return response
        
        return "يمكنني مساعدتك في معرفة عدد الأصول. هل تقصد عدد الأصول الكلي؟"
    
    def handle_cost_questions(self, question):
        """معالجة الأسئلة المتعلقة بالتكلفة والقيمة"""
        if not self.cost_converted:
            return "⚠️ عذراً، لا توجد بيانات مالية متاحة للتحليل."
        
        if 'إجمالي' in question or 'كلي' in question or 'مجموع' in question:
            return f"**إجمالي قيمة الأصول:** {self.total_cost:,.0f} ريال\n\n**صافي القيمة الدفترية:** {self.total_nbv:,.0f} ريال"
        
        elif 'متوسط' in question or 'معدل' in question:
            avg_cost = self.total_cost / self.total_assets if self.total_assets > 0 else 0
            return f"**متوسط تكلفة الأصل الواحد:** {avg_cost:,.0f} ريال"
        
        elif 'أعلى' in question or 'أغلى' in question:
            top_assets = self.df_processed.nlargest(5, self.cost_col)
            response = "**أغلى 5 أصول:**\n"
            for idx, asset in top_assets.iterrows():
                asset_name = asset.get(self.desc_col, 'غير محدد')
                cost = asset.get(self.cost_col, 0)
                response += f"\n• {asset_name}: {cost:,.0f} ريال"
            return response
        
        return f"إجمالي تكلفة جميع الأصول: **{self.total_cost:,.0f} ريال**"
    
    def handle_location_questions(self, question):
        """معالجة الأسئلة المتعلقة بالمواقع"""
        if self.city_col not in self.df_processed.columns:
            return "⚠️ لا توجد بيانات عن مواقع الأصول."
        
        cities = self.df_processed[self.city_col].dropna().unique()
        
        if 'أين' in question or 'مكان' in question:
            # البحث عن أصل محدد في السؤال
            for word in question.split():
                if len(word) > 2:
                    found_assets = self.df_processed[
                        self.df_processed[self.desc_col].astype(str).str.contains(word, na=False) |
                        self.df_processed[self.tag_col].astype(str).str.contains(word, na=False)
                    ]
                    if not found_assets.empty:
                        asset = found_assets.iloc[0]
                        location = asset.get(self.city_col, 'غير محدد')
                        building = asset.get(self.building_col, 'غير محدد')
                        return f"**الموقع:** {location} - {building}"
            
            return "يرجى تحديد الأصل الذي تبحث عنه (رقم الوسم أو الوصف)"
        
        return f"**المدن المتاحة:** {', '.join([str(c) for c in cities])}"
    
    def handle_search_questions(self, question):
        """معالجة أسئلة البحث"""
        # استخراج كلمات البحث من السؤال
        search_terms = []
        for word in question.split():
            if len(word) > 2 and word not in ['ابحث', 'عن', 'عرض', 'أرني', 'اظهر']:
                search_terms.append(word)
        
        if not search_terms:
            return "يرجى تحديد ما تريد البحث عنه (مثال: ابحث عن أجهزة كمبيوتر)"
        
        # البحث في البيانات
        results = []
        for term in search_terms:
            mask = (
                self.df_processed[self.desc_col].astype(str).str.contains(term, na=False, case=False) |
                self.df_processed[self.tag_col].astype(str).str.contains(term, na=False, case=False) |
                self.df_processed[self.unique_asset_col].astype(str).str.contains(term, na=False, case=False)
            )
            results.extend(self.df_processed[mask].to_dict('records'))
        
        if results:
            response = f"**تم العثور على {len(results)} نتيجة:**\n"
            for i, asset in enumerate(results[:5], 1):  # عرض أول 5 نتائج فقط
                desc = asset.get(self.desc_col, 'غير محدد')
                tag = asset.get(self.tag_col, 'غير محدد')
                cost = asset.get(self.cost_col, 0)
                response += f"\n{i}. {desc} (الوسم: {tag}) - {cost:,.0f} ريال"
            
            if len(results) > 5:
                response += f"\n\n... وعرض {len(results) - 5} نتيجة إضافية"
            
            return response
        else:
            return "❌ لم يتم العثور على نتائج تطابق بحثك."
    
    def handle_summary_questions(self, question):
        """معالجة أسئلة الملخص والإحصائيات"""
        response = f"**ملخص شامل للأصول:**\n\n"
        response += f"• إجمالي عدد الأصول: **{self.total_assets:,}**\n"
        response += f"• إجمالي التكلفة: **{self.total_cost:,.0f} ريال**\n"
        response += f"• صافي القيمة الدفترية: **{self.total_nbv:,.0f} ريال**\n"
        
        if self.cost_converted and self.nbv_converted:
            depreciation = self.total_cost - self.total_nbv
            dep_rate = (depreciation / self.total_cost * 100) if self.total_cost > 0 else 0
            response += f"• إجمالي الاستهلاك: **{depreciation:,.0f} ريال**\n"
            response += f"• معدل الاستهلاك: **{dep_rate:.1f}%**\n"
        
        if self.city_col in self.df_processed.columns:
            city_stats = self.df_processed[self.city_col].value_counts().head(3)
            response += f"\n**أهم المدن:**\n"
            for city, count in city_stats.items():
                response += f"• {city}: {count} أصل\n"
        
        return response
    
    def handle_depreciation_questions(self, question):
        """معالجة أسئلة الاستهلاك والقيمة المتبقية"""
        if not self.cost_converted or not self.nbv_converted:
            return "⚠️ لا توجد بيانات مالية كافية لتحليل الاستهلاك."
        
        df_analysis = self.df_processed.dropna(subset=[self.cost_col, self.nbv_col])
        df_analysis = df_analysis[df_analysis[self.cost_col] > 0]
        
        if df_analysis.empty:
            return "❌ لا توجد بيانات صالحة لتحليل الاستهلاك."
        
        df_analysis['Depreciation Rate'] = (
            (df_analysis[self.cost_col] - df_analysis[self.nbv_col]) / df_analysis[self.cost_col] * 100
        ).round(1)
        
        high_dep = len(df_analysis[df_analysis['Depreciation Rate'] > 50])
        avg_dep = df_analysis['Depreciation Rate'].mean()
        
        response = f"**تحليل الاستهلاك:**\n\n"
        response += f"• متوسط معدل الاستهلاك: **{avg_dep:.1f}%**\n"
        response += f"• عدد الأصول عالية الاستهلاك (أكثر من 50%): **{high_dep}**\n"
        
        # الأصول الأكثر استهلاكاً
        high_dep_assets = df_analysis.nlargest(3, 'Depreciation Rate')
        if not high_dep_assets.empty:
            response += f"\n**أكثر الأصول استهلاكاً:**\n"
            for idx, asset in high_dep_assets.iterrows():
                desc = asset.get(self.desc_col, 'غير محدد')
                dep_rate = asset['Depreciation Rate']
                response += f"• {desc}: {dep_rate}%\n"
        
        return response
    
    def handle_city_questions(self, question):
        """معالجة الأسئلة المتعلقة بالمدن"""
        if self.city_col not in self.df_processed.columns:
            return "⚠️ لا توجد بيانات عن المدن."
        
        # استخراج اسم المدينة من السؤال
        cities_in_data = self.df_processed[self.city_col].dropna().unique()
        mentioned_city = None
        
        for city in cities_in_data:
            if str(city).lower() in question.lower():
                mentioned_city = city
                break
        
        if mentioned_city:
            city_assets = self.df_processed[self.df_processed[self.city_col] == mentioned_city]
            city_count = len(city_assets)
            city_cost = city_assets[self.cost_col].sum() if self.cost_converted else 0
            
            response = f"**إحصائيات {mentioned_city}:**\n\n"
            response += f"• عدد الأصول: **{city_count}**\n"
            response += f"• إجمالي التكلفة: **{city_cost:,.0f} ريال**\n"
            
            # أنواع الأصول في المدينة
            if self.desc_col in city_assets.columns:
                common_assets = city_assets[self.desc_col].value_counts().head(3)
                if not common_assets.empty:
                    response += f"\n**أكثر أنواع الأصول شيوعاً:**\n"
                    for asset_type, count in common_assets.items():
                        response += f"• {asset_type}: {count}\n"
            
            return response
        else:
            city_stats = self.df_processed[self.city_col].value_counts()
            response = "**توزيع الأصول حسب المدينة:**\n\n"
            for city, count in city_stats.head(5).items():
                response += f"• {city}: {count} أصل\n"
            
            return response
    
    def handle_top_questions(self, question):
        """معالجة أسئلة الأعلى والأكبر"""
        if not self.cost_converted:
            return "⚠️ لا توجد بيانات مالية للتحليل."
        
        n = 5  # عدد النتائج الافتراضي
        
        if '3' in question:
            n = 3
        elif '10' in question:
            n = 10
        
        top_assets = self.df_processed.nlargest(n, self.cost_col)
        
        response = f"**أغلى {n} أصول:**\n\n"
        for i, (idx, asset) in enumerate(top_assets.iterrows(), 1):
            desc = asset.get(self.desc_col, 'غير محدد')
            tag = asset.get(self.tag_col, 'غير محدد')
            cost = asset.get(self.cost_col, 0)
            nbv = asset.get(self.nbv_col, 0)
            
            response += f"{i}. **{desc}**\n"
            response += f"   - الوسم: {tag}\n"
            response += f"   - التكلفة: {cost:,.0f} ريال\n"
            response += f"   - القيمة الدفترية: {nbv:,.0f} ريال\n\n"
        
        return response
    
    def handle_general_questions(self, question):
        """معالجة الأسئلة العامة"""
        general_responses = [
            "يمكنني مساعدتك في:\n• معرفة عدد الأصول وتكلفتها\n• البحث عن أصول محددة\n• تحليل الاستهلاك والقيمة\n• توزيع الأصول جغرافياً\n\nما الذي تريد معرفته؟",
            "أنا مساعدك الذكي لفهم بيانات الأصول. اسألني عن:\n- الإحصائيات العامة\n- تكاليف الأصول\n- مواقع التوزيع\n- تحليل الاستهلاك",
            "مرحباً! أنا هنا لمساعدتك في تحليل بيانات الأصول. جرب أن تسأل:\n'كم عدد الأصول؟'\n'ما إجمالي التكلفة؟'\n'أين توجد أجهزة الكمبيوتر؟'"
        ]
        
        return np.random.choice(general_responses)

# إنشاء المساعد الذكي
ai_assistant = AssetAIAssistant(df)

# واجهة المساعد الذكي
def ai_chat_interface():
    st.markdown("---")
    st.markdown('<div class="ai-assistant">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white;'>🤖 مساعد الأصول الذكي</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # تهيئة سجل المحادثة
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # عرض سجل المحادثة
    st.markdown("### 💬 محادثتك")
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message['type'] == 'user':
                st.markdown(f'<div class="user-message"><strong>أنت:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-response"><strong>المساعد:</strong> {message["content"]}</div>', unsafe_allow_html=True)
    
    # أمثلة للأسئلة
    st.markdown("### 💡 أمثلة للأسئلة التي يمكنك طرحها:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("كم عدد الأصول؟", use_container_width=True):
            st.session_state.quick_question = "كم عدد الأصول؟"
    
    with col2:
        if st.button("ما إجمالي التكلفة؟", use_container_width=True):
            st.session_state.quick_question = "ما إجمالي التكلفة؟"
    
    with col3:
        if st.button("أعرض ملخص عام", use_container_width=True):
            st.session_state.quick_question = "أعرض ملخص عام"
    
    # مدخل السؤال
    st.markdown("### 💭 اكتب سؤالك هنا:")
    question = st.text_input(
        "اسألني عن أي شيء يتعلق بالأصول...",
        placeholder="مثال: كم عدد الأصول في الرياض؟ أو ما هي أغلى الأصول؟",
        key="question_input"
    )
    
    # معالجة السؤال
    if st.button("إرسال السؤال", type="primary", use_container_width=True) or 'quick_question' in st.session_state:
        if 'quick_question' in st.session_state:
            question = st.session_state.quick_question
            del st.session_state.quick_question
        
        if question.strip():
            # إضافة سؤال المستخدم للسجل
            st.session_state.chat_history.append({
                'type': 'user',
                'content': question,
                'timestamp': datetime.now()
            })
            
            # توليد الرد
            with st.spinner("🤔 المساعد يفكر..."):
                response = ai_assistant.generate_response(question)
            
            # إضافة رد المساعد للسجل
            st.session_state.chat_history.append({
                'type': 'assistant',
                'content': response,
                'timestamp': datetime.now()
            })
            
            # إعادة تحميل الصفحة لعرض الرد الجديد
            st.rerun()
    
    # خيارات إضافية
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ مسح المحادثة", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    
    with col2:
        if st.button("📊 عرض تقرير مفصل", use_container_width=True):
            st.session_state.chat_history.append({
                'type': 'user',
                'content': "أعطني تقرير مفصل عن جميع الأصول",
                'timestamp': datetime.now()
            })
            
            detailed_report = ai_assistant.handle_summary_questions("تقرير مفصل")
            st.session_state.chat_history.append({
                'type': 'assistant',
                'content': detailed_report,
                'timestamp': datetime.now()
            })
            st.rerun()

# العرض حسب الوضع المختار
if display_mode == "المساعد الذكي":
    ai_chat_interface()
elif display_mode == "لوحة التحكم":
    # ... (كود لوحة التحكم السابق)
    st.info("🚀 استخدم المساعد الذكي للحصول على إجابات فورية عن بياناتك!")
elif display_mode == "التحليل المالي":
    # ... (كود التحليل المالي السابق) 
    st.info("💬 جرب المساعد الذكي لطرح أسئلة محددة عن تحليلاتك!")
else:
    ai_chat_interface()
    st.markdown("---")
    # ... (إضافة باقي الوظائف)

# تذييل الصفحة
st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px;">'
    '<h3 style="margin:0;">✅ الإصدار 7.0 - المساعد الذكي</h3>'
    '<p style="margin:5px 0 0 0;">اسألني عن أي شيء في بيانات الأصول!</p>'
    '</div>', 
    unsafe_allow_html=True
)
