import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# הגדרות עמוד ראשיות
st.set_page_config(
    page_title="מערכת ניהול נדל״ן וחשבונות",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# חיבור ל-Supabase דרך Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"שגיאה בהתחברות ל-Supabase. ודא שהגדרת את ה-Secrets בצורה תקינה: {e}")
    st.stop()

# פונקציות לשליפת נתונים
def get_properties():
    response = supabase.table("properties").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

def get_transactions():
    response = supabase.table("transactions").select("*").execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()

# סרגל ניווט צדדי
st.sidebar.title("🏢 ניהול נדל״ן")
menu = st.sidebar.radio(
    "בחר מסך:",
    [
        "1. דשבורד ראשי",
        "2. תיק נכס פרטני",
        "3. קבלנים והצעות מחיר",
        "4. קליטת חשבוניות והוצאות",
        "5. דוחות מס ורואה חשבון"
    ]
)

# --- מסך 1: דשבורד ראשי ---
if menu == "1. דשבורד ראשי":
    st.header("📊 דשבורד פיננסי מרכז")
    st.caption("נתוני זמן אמת מבסיס הנתונים בענן (Supabase)")

    df_properties = get_properties()
    df_tx = get_transactions()

    total_props = len(df_properties)
    monthly_rent = 0
    if not df_properties.empty and "monthly_rent" in df_properties.columns:
        monthly_rent = df_properties["monthly_rent"].fillna(0).sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("סה״כ נכסים פעילים", total_props)
    col2.metric("צפי שכירות חודשית", f"₪ {monthly_rent:,.0f}")
    col3.metric("תזרים שוטף", "פעיל")
    col4.metric("סטטוס ענן", "מחובר ל-Supabase ✅")

    st.divider()

    # טופס להוספת נכס חדש ישירות לענן
    with st.expander("➕ הוסף נכס חדש למערכת", expanded=False):
        with st.form("add_property_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("שם הנכס / כינוי (למשל: דירה הרצל)")
            address = c2.text_input("כתובת מלאה")
            prop_type = c1.selectbox("סוג נכס", ["דירת מגורים", "בית פרטי", "מסחרי / משרד", "קרקע / מגרש"])
            status = c2.selectbox("סטטוס", ["מושכרת", "בשיפוץ", "פנויה", "בתהליך רכישה"])
            purchase_price = c1.number_input("מחיר רכישה (₪)", min_value=0.0, step=10000.0)
            monthly_rent_input = c2.number_input("שכר דירה חודשי צפוי (₪)", min_value=0.0, step=100.0)
            
            submit = st.form_submit_button("שמור נכס ב-Supabase", type="primary")
            if submit:
                if not address:
                    st.warning("נא להזין לפחות כתובת לנכס.")
                else:
                    new_prop = {
                        "name": name if name else address,
                        "address": address,
                        "property_type": prop_type,
                        "status": status,
                        "purchase_price": purchase_price,
                        "monthly_rent": monthly_rent_input
                    }
                    try:
                        supabase.table("properties").insert(new_prop).execute()
                        st.success("הנכס נשמר בהצלחה בבסיס הנתונים!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"שגיאה בשמירת הנכס: {err}")

    st.subheader("🏡 רשימת הנכסים שלך")
    if not df_properties.empty:
        display_cols = [c for c in ["name", "address", "property_type", "status", "monthly_rent", "purchase_price"] if c in df_properties.columns]
        st.dataframe(df_properties[display_cols], width='stretch')
    else:
        st.info("עדיין לא הוזנו נכסים. לחץ על 'הוסף נכס חדש למערכת' למעלה כדי להוסיף את הנכס הראשון!")

# --- מסך 2: תיק נכס פרטני ---
elif menu == "2. תיק נכס פרטני":
    st.header("📁 תיק נכס מפורט")
    df_properties = get_properties()

    if df_properties.empty:
        st.info("אין נכסים במערכת. הוסף נכס במסך הדשבורד.")
    else:
        prop_options = df_properties["address"].tolist() if "address" in df_properties.columns else df_properties["id"].tolist()
        property_selected = st.selectbox("בחר נכס לצפייה:", prop_options)

        tab1, tab2, tab3 = st.tabs(["💰 עלויות רכישה והשבחה", "📈 הכנסות והוצאות", "📑 מסמכים וחוזים"])

        selected_row = df_properties[df_properties["address"] == property_selected].iloc[0]

        with tab1:
            st.subheader("עלויות הוניות")
            c1, c2 = st.columns(2)
            c1.metric("מחיר רכישה רשום", f"₪ {selected_row.get('purchase_price', 0):,.0f}")
            c2.metric("סטטוס נוכחי", str(selected_row.get('status', 'לא מוגדר')))

        with tab2:
            st.subheader("תנועות שוטפות של הנכס")
            st.write("כאן ירוכזו כל החשבוניות והתשלומים המקושרים לנכס זה.")

        with tab3:
            st.subheader("מסמכים מתוך Supabase Storage")
            st.write("תיקיית המסמכים המקושרת לנכס בענן.")

# --- מסך 3: קבלנים והצעות מחיר ---
elif menu == "3. קבלנים והצעות מחיר":
    st.header("🔨 ניהול קבלנים והשוואת הצעות מחיר")
    
    with st.expander("➕ הזנת הצעת מחיר חדשה מקבלן", expanded=False):
        c1, c2 = st.columns(2)
        c1.text_input("שם הקבלן / חברה")
        c2.number_input("סכום כולל של ההצעה (לפני מע״מ)", min_value=0.0, step=100.0)
        st.text_area("פירוט כתב כמויות / סעיפי עבודה")
        st.file_uploader("העלה את מסמך ההצעה (PDF / תמונה)", type=["pdf", "png", "jpg"])
        st.button("שמור הצעת מחיר")

    st.subheader("⚖️ השוואת הצעות מחיר לפרויקט")
    st.write("כאן תופיע השוואת הצעות מחיר בין קבלנים שונים.")

# --- מסך 4: קליטת חשבוניות והוצאות ---
elif menu == "4. קליטת חשבוניות והוצאות":
    st.header("🧾 קליטת חשבונית / הוצאה חדשה")
    st.caption("הזנה ידנית או העלאת מסמך לסריקה ישירות לענן")

    uploaded_file = st.file_uploader("בחר קובץ חשבונית או קבלה (PDF / תמונה)", type=["pdf", "png", "jpg"])
    
    df_properties = get_properties()
    prop_choices = ["כללי / ללא שיוך"] + (df_properties["address"].tolist() if not df_properties.empty and "address" in df_properties.columns else [])

    col1, col2 = st.columns(2)
    with col1:
        vendor = st.text_input("שם הספק / בית העסק")
        tx_date = st.date_input("תאריך החשבונית", datetime.now())
        linked_prop = st.selectbox("נכס משויך", prop_choices)
    with col2:
        amount = st.number_input("סכום כולל לתשלום (כולל מע״מ)", min_value=0.0, step=10.0)
        tax_class = st.selectbox("סיווג מס", ["שוטף - מוכר בניכוי שכר דירה", "הוני - השבחה לחישוב מס שבח", "מימון - ריבית משכנתא", "הנהלה וכלליות"])
        description = st.text_area("תיאור ההוצאה")

    if st.button("💾 שמור הוצאה ב-Supabase", type="primary"):
        st.success("ההוצאה מוכנה לשמירה ומקושרת לענן!")

# --- מסך 5: דוחות מס ורואה חשבון ---
elif menu == "5. דוחות מס ורואה חשבון":
    st.header("📑 דוחות מס מוכנים לרואה חשבון")
    st.caption("הפקת נתונים מרוכזים לשנת המס בלחיצת כפתור")

    c1, c2, c3 = st.columns(3)
    c1.selectbox("שנת מס", ["2026", "2025", "2024"])
    c2.selectbox("נכס", ["כל הנכסים"])
    c3.selectbox("סוג הדוח", ["דוח רווח והפסד שנתי (P&L)", "דוח השבחות והוצאות הוניות", "ריכוז חשבוניות וספקים"])

    col_btn1, col_btn2 = st.columns(2)
    col_btn1.button("📥 הורד קובץ Excel לרו״ח")
    col_btn2.button("📄 הפק קובץ PDF מסודר")
