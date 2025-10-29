
import pandas as pd
import re

# Try to standardize Arabic column names to internal keys
COMMON_HEADERS = {
    "Asset Unique No": ["رقم الأصل الفريد", "رقم الأصل الفريد بالجهة", "الرقم التسلسلي", "Unique Asset Number", "Unique Asset Number in the entity"],
    "Description": ["وصف الأصل","Asset Description","Asset Description For Maintenance Purpose","الوصف"],
    "Tag Number": ["Tag number","رقم البطاقة","الوسم","الباركود"],
    "Unit of Measure": ["وحدة القياس","Base Unit of Measure"],
    "Quantity": ["العدد","Quantity"],
    "Manufacturer": ["المصنع","Manufacturer"],
    "Date Placed in Service": ["تاريخ الدخول في الخدمة","Date Placed in Service"],
    "Cost": ["التكلفة","Cost"],
    "Depreciation Expense": ["قسط الاهلاك","Depreciation amount","Depreciation Expense"],
    "Accumulated Depreciation": ["الاستهلاك المتراكم","Accumulated Depreciation"],
    "Residual Value": ["Residual Value","القيمة المتبقية"],
    "Net Book Value": ["Net Book Value","القيمة الدفترية"],
    "Useful Life": ["العمر الإنتاجي","Useful Life"],
    "Remaining Life": ["Remaining useful life","المتبقي"],
    "Country": ["الدولة","Country"],
    "Region": ["المنطقة","Region"],
    "City": ["المدينة","City"],
    "Coordinates": ["الإحداثيات","إحداثيات","Geographical Coordinates"],
    "Building": ["رقم المبنى","Building Number","Building"],
    "Floor": ["رقم الدور","Floors Number","Floor"],
    "Room/Office": ["رقم الغرفة/المكتب","Room/office Number","Room"],
    "Entity Name": ["اسم الجهة"],
    "Entity Code": ["رمز الجهة"],
    "Accounting Group Code": ["رمز المجموعة المحاسبية","GL account","accounting group code"],
    "Accounting Group Desc": ["وصف المجموعة المحاسبية","accounting group"]
}

def normalize_colname(c):
    c = str(c).strip()
    c = re.sub(r"\s+", " ", c)
    return c

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # drop unnamed empty columns
    cols = [c for c in df.columns if not (str(c).startswith("Unnamed") or str(c).strip()=="")]
    df = df[cols].copy()
    df.columns = [normalize_colname(c) for c in df.columns]
    return df

def guess_columns(columns):
    # Try to map internal keys to real columns by fuzzy name match
    colmap = {}
    for key, variants in COMMON_HEADERS.items():
        chosen = None
        # exact match
        for v in variants:
            for c in columns:
                if normalize_colname(c) == normalize_colname(v):
                    chosen = c
                    break
            if chosen:
                break
        # contains match
        if not chosen:
            for v in variants:
                for c in columns:
                    if normalize_colname(v) in normalize_colname(c):
                        chosen = c
                        break
                if chosen:
                    break
        colmap[key] = chosen if chosen in columns else None
    return colmap

def parse_coordinates(text):
    """Parse 'lat,lon' into floats. Returns (lat, lon) or (None, None)."""
    if text is None:
        return (None, None)
    s = str(text).strip()
    s = s.replace("،", ",")  # Arabic comma
    parts = [p.strip() for p in s.split(",")]
    if len(parts) != 2:
        return (None, None)
    try:
        lat = float(parts[0])
        lon = float(parts[1])
        if abs(lat) > 90 or abs(lon) > 180:
            return (None, None)
        return (lat, lon)
    except Exception:
        return (None, None)
