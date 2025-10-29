
from fpdf import FPDF
from bidi.algorithm import get_display
import arabic_reshaper
from io import BytesIO
import qrcode
from datetime import datetime

# Helper: reshape & bidi Arabic text
def ar(text):
    if text is None:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

class AssetPDF(FPDF):
    def header(self):
        self.set_font("Arial", "", 10)
        self.cell(0, 8, ar("ورقة بيانات الأصل"), 0, 1, "R")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"{datetime.now():%Y-%m-%d %H:%M}", 0, 0, "L")
        self.cell(0, 10, "Page " + str(self.page_no()) + "/{nb}", 0, 0, "R")

def make_asset_pdf(record: dict, colmap: dict) -> bytes:
    pdf = AssetPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Add Arabic-capable font (built-in Arial doesn't support Arabic shaping, but we will reshape+bidi)
    # For best results, embed a TTF like Tajawal if available.
    # Here we rely on reshaping + bidi with default font.
    pdf.set_font("Arial","",12)

    # Title
    pdf.set_font("Arial","B",14)
    pdf.cell(0, 10, ar("بيانات الأصل التفصيلية"), 0, 1, "R")
    pdf.ln(2)

    def row(k, key):
        v = record.get(colmap.get(key), "")
        pdf.set_font("Arial","B",11); pdf.cell(60, 8, ar(k), 0, 0, "R")
        pdf.set_font("Arial","",11);   pdf.cell(0, 8, ar(v), 0, 1, "R")

    # Sections
    pdf.set_font("Arial","B",12); pdf.cell(0, 8, ar("أولاً: بيانات التعريف"), 0, 1, "R")
    for k, key in [("اسم الجهة","Entity Name"),("رمز الجهة","Entity Code"),
                   ("رقم الأصل الفريد","Asset Unique No"),("رقم البطاقة/الوسم","Tag Number"),
                   ("رمز المجموعة المحاسبية","Accounting Group Code"),("وصف المجموعة المحاسبية","Accounting Group Desc")]:
        row(k, key)

    pdf.ln(2)
    pdf.set_font("Arial","B",12); pdf.cell(0, 8, ar("ثانياً: المواصفات"), 0, 1, "R")
    for k, key in [("وصف الأصل","Description"),("المصنّع","Manufacturer"),
                   ("وحدة القياس","Unit of Measure"),("العدد","Quantity")]:
        row(k, key)

    pdf.ln(2)
    pdf.set_font("Arial","B",12); pdf.cell(0, 8, ar("ثالثاً: القيم المالية"), 0, 1, "R")
    for k, key in [("التكلفة","Cost"),("قسط الاهلاك","Depreciation Expense"),
                   ("الاستهلاك المتراكم","Accumulated Depreciation"),
                   ("القيمة المتبقية","Residual Value"),("القيمة الدفترية","Net Book Value")]:
        row(k, key)

    pdf.ln(2)
    pdf.set_font("Arial","B",12); pdf.cell(0, 8, ar("رابعاً: الموقع"), 0, 1, "R")
    for k, key in [("الدولة","Country"),("المنطقة","Region"),("المدينة","City"),
                   ("رقم المبنى","Building"),("رقم الدور","Floor"),
                   ("رقم الغرفة/المكتب","Room/Office"),("الإحداثيات","Coordinates")]:
        row(k, key)

    # QR code with Asset ID
    asset_id = record.get(colmap.get("Asset Unique No"), "")
    if asset_id:
        qr = qrcode.QRCode(box_size=3, border=2)
        qr.add_data(str(asset_id)); qr.make(fit=True)
        img = qr.make_image()
        buf = BytesIO()
        img.save(buf, format="PNG"); buf.seek(0)
        x = pdf.get_x(); y = pdf.get_y()
        pdf.image(buf, x=10, y=y, w=25)  # place qr on left bottom
        pdf.set_y(y + 30)

    out = pdf.output(dest="S").encode("latin1", "ignore")
    return out
