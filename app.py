import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

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
    st.error(f"שגיאה בהתחברות ל-Supabase: {e}")
    st.stop()

# שליפת נתונים
def get_properties():
    try:
        response = supabase.table("properties").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# סרגל ניווט
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
    st.caption("נתוני אמת מחוברים ל-Supabase בענן")

    df_properties = get_properties()

    total_props = len(df_properties)
    
    # חישוב שווי כולל
    total_val_usd = 0.0
    total_val_ils = 0.0
    if not df_properties.empty and "purchase_price" in df_properties.columns:
        for _, row in df_properties.iterrows():
            price = float(row.get("purchase_price") or 0)
            curr = row.get("currency", "$")
            if curr == "$":
                total_val_usd += price
            else:
                total_val_ils += price

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("סה״כ נכסים פעילים", total_props)
    
    if total_val_usd > 0 and total_val_ils > 0:
        col2.metric("שווי רכישה כולל", f"${total_val_usd:,.0f} | ₪{total_val_ils:,.0f}")
    elif total_val_usd > 0:
        col2.metric("שווי רכישה כולל", f"${total_val_usd:,.0f}")
    else:
        col2.metric("שווי רכישה כולל", f"₪{total_val_ils:,.0f}")

    col3.metric("תזרים שוטף", "פעיל")
    col4.metric("סטטוס ענן", "מחובר ל-Supabase ✅")

    st.divider()

    # טופס הוספת נכס
    with st.expander("➕ הוסף נכס חדש למערכת", expanded=False):
        with st.form("add_property_form"):
            c1, c2, c3 = st.columns([2, 2, 1])
            name = c1.text_input("שם הנכס / כינוי (למשל: Sylvan Ave)")
            address = c2.text_input("כתובת מלאה (למשל: 1330 Sylvan Ave Homestead, PA)")
            currency = c3.selectbox("מטבע", ["$", "₪"])

            c4, c5 = st.columns(2)
            prop_type = c4.selectbox("סוג נכס", ["בית פרטי (Single Family)", "בניין דירות (Multi-family)", "דירת מגורים", "מסחרי / משרד", "קרקע"])
            status = c5.selectbox("סטטוס", ["בשיפוץ", "מושכרת", "פנויה", "בתהליך רכישה"])

            c6, c7 = st.columns(2)
            purchase_price = c6.number_input(f"מחיר רכישה ({currency})", min_value=0.0, step=1000.0)
            target_rent = c7.number_input(f"שכר דירה חודשי צפוי ({currency})", min_value=0.0, step=50.0)

            submit = st.form_submit_button("שמור נכס ב-Supabase", type="primary")
            if submit:
                if not address:
                    st.warning("נא להזין כתובת לנכס.")
                else:
                    new_prop = {
                        "name": name if name else address,
                        "address": address,
                        "property_type": prop_type,
                        "status": status,
                        "purchase_price": purchase_price,
                        "currency": currency
                    }
                    # ניסיון שמירה מותאם לעמודות הקיימות
                    try:
                        # בדיקה ושמירה כולל שכר דירה
                        new_prop["monthly_rent"] = target_rent
                        supabase.table("properties").insert(new_prop).execute()
                        st.success("הנכס נשמר בהצלחה בבסיס הנתונים!")
                        st.rerun()
                    except Exception:
                        try:
                            # אם אין עמודת monthly_rent ננסה target_rent או ללא שדה זה
                            del new_prop["monthly_rent"]
                            new_prop["target_rent"] = target_rent
                            supabase.table("properties").insert(new_prop).execute()
                            st.success("הנכס נשמר בהצלחה בבסיס הנתונים!")
                            st.rerun()
                        except Exception:
                            # שמירה עם שדות הבסיס בלבד
                            new_prop.pop("target_rent", None)
                            supabase.table("properties").insert(new_prop).execute()
                            st.success("הנכס נשמר בהצלחה בבסיס הנתונים!")
                            st.rerun()

    st.subheader("🏡 רשימת הנכסים שלך")
    if not df_properties.empty:
        # עיצוב תצוגת הטבלה עם המטבע המתאים
        cols_to_show = [c for c in ["name", "address", "property_type", "status", "currency", "purchase_price"] if c in df_properties.columns]
        st.dataframe(df_properties[cols_to_show], width='stretch')
    else:
        st.info("עדיין לא הוזנו נכסים. לחץ על 'הוסף נכס חדש למערכת' כדי להוסיף את הנכס הראשון.")

# --- מסך 2: תיק נכס פרטני ---
elif menu == "2. תיק נכס פרטני":
    st.header("📁 תיק נכס מפורט")
    df_properties = get_properties()

    if df_properties.empty:
        st.info("אין עדיין נכסים במערכת.")
    else:
        prop_labels = df_properties["name"].tolist() if "name" in df_properties.columns else df_properties["address"].tolist()
        selected_name = st.selectbox("בחר נכס לצפייה:", prop_labels)
        selected_prop = df_properties[df_properties["name"] == selected_name].iloc[0]

        curr_symbol = selected_prop.get("currency", "$")
        c1, c2, c3 = st.columns(3)
        c1.metric("כתובת", str(selected_prop.get("address", "")))
        c2.metric("סטטוס", str(selected_prop.get("status", "")))
        c3.metric("מחיר רכישה", f"{curr_symbol} {selected_prop.get('purchase_price', 0):,.0f}")

        tab1, tab2, tab3 = st.tabs(["💰 פירוט השקעה", "📑 תנועות שוטפות", "📂 מסמכים וחוזים"])
        with tab1:
            st.write("פרטי רכישה והשבחה של הנכס.")
        with tab2:
            st.write("הכנסות שכר דירה והוצאות תחזוקה.")
        with tab3:
            st.write("מסמכי טאבו, ביטוח וחוזים מתוך Supabase Storage.")

# --- מסך 3: קבלנים והצעות מחיר ---
elif menu == "3. קבלנים והצעות מחיר":
    st.header("🔨 ניהול קבלנים והשוואת הצעות מחיר")
    st.info("מסך השוואת הצעות מחיר לקראת שיפוץ והשבחה.")

# --- מסך 4: קליטת חשבוניות והוצאות ---
elif menu == "4. קליטת חשבוניות והוצאות":
    st.header("🧾 קליטת חשבונית / הוצאה")
    df_properties = get_properties()
    prop_choices = ["כללי"] + (df_properties["name"].tolist() if not df_properties.empty and "name" in df_properties.columns else [])
    
    c1, c2 = st.columns(2)
    c1.text_input("שם הספק")
    c1.date_input("תאריך", datetime.now())
    c2.selectbox("שיוך לנכס", prop_choices)
    c2.selectbox("מטבע", ["$", "₪"])
    c2.number_input("סכום", min_value=0.0, step=10.0)
    st.file_uploader("צרף קובץ חשבונית / קבלה", type=["pdf", "png", "jpg"])
    st.button("שמור הוצאה")

# --- מסך 5: דוחות מס ורואה חשבון ---
elif menu == "5. דוחות מס ורואה חשבון":
    st.header("📑 דוחות מס ורואה חשבון")
    c1, c2 = st.columns(2)
    c1.selectbox("שנת מס", ["2026", "2025"])
    c2.selectbox("מטבע הדוח", ["USD ($)", "ILS (₪)"])
    st.button("הפק דוח רווח והפסד שנתי")
