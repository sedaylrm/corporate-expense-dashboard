import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract
import re
import sqlite3
from datetime import datetime, date
from google import genai

# --- SAYFA YAPILANDIRMASI VE GELİŞMİŞ WEB CSS MAKYAJI ---
st.set_page_config(page_title="Corporate Expense Automation & Auth", page_icon="🧾", layout="wide")

st.markdown("""
    <style>
    .main {
        background-color: #f4f6f9;
    }
    div.block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        color: #0f172a;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# --- API ANAHTARI VE YAPAY ZEKA YAPILANDIRMASI ---
GEMINI_API_KEY = "BURAYA_GEMINI_API_KEY_GIRINIZ"

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    client = None

# --- TESSERACT YOLU TANIMLAMASI ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- VERİTABANI BAĞLANTISI VE OLUŞTURMA ---
def init_db():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            date TEXT,
            amount REAL,
            category TEXT,
            raw_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- KULLANICI İŞLEMLERİ ---
def register_user(username, password):
    try:
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def add_expense(username, date_str, amount, category, raw_text):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (username, date, amount, category, raw_text) VALUES (?, ?, ?, ?, ?)', 
              (username, date_str, amount, category, raw_text))
    conn.commit()
    conn.close()

def get_user_expenses(username):
    conn = sqlite3.connect('expenses.db')
    df = pd.read_sql_query(
        "SELECT id, date as 'Tarih', amount as 'Tutar (TL)', category as 'Kategori' FROM expenses WHERE username = ?", 
        conn, 
        params=(username,)
    )
    conn.close()
    return df

def clear_user_db(username):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE username = ?', (username,))
    conn.commit()
    conn.close()

# Oturum Durumu Yönetimi
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- GİRİŞ / KAYIT EKRANI ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    
    with col_center2:
        with st.container():
            st.markdown("### 🔐 Kurumsal Masraf Otomasyonu")
            st.write("Devam etmek için hesabınıza giriş yapın veya yeni kayıt oluşturun.")
            
            tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
            
            with tab1:
                st.subheader("Hesaba Giriş")
                login_user = st.text_input("Kullanıcı Adı", key="login_user")
                login_pass = st.text_input("Şifre", type="password", key="login_pass")
                
                if st.button("Giriş Yap", use_container_width=True):
                    if verify_user(login_user, login_pass):
                        st.session_state.logged_in = True
                        st.session_state.username = login_user
                        st.success(f"Hoş geldiniz, {login_user}!")
                        st.rerun()
                    else:
                        st.error("Kullanıcı adı veya şifre hatalı!")
                        
            with tab2:
                st.subheader("Hesap Oluştur")
                new_user = st.text_input("Kullanıcı Adı", key="new_user")
                new_pass = st.text_input("Şifre", type="password", key="new_pass")
                
                if st.button("Kayıt Ol", use_container_width=True):
                    if new_user and new_pass:
                        if register_user(new_user, new_pass):
                            st.success("Hesap başarıyla oluşturuldu! Giriş yapabilirsiniz.")
                        else:
                            st.error("Bu kullanıcı adı zaten alınmış.")
                    else:
                        st.warning("Lütfen alanları doldurun.")

else:
    # --- ANA UYGULAMA (GİRİŞ YAPILDIKTAN SONRA) ---
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.markdown("---")
    
    # --- 🤖 SOL MENÜDEKİ AI FİNANSAL ASİSTAN (SOHBET KUTUSU) ---
    st.sidebar.subheader("💬 AI Finansal Asistan")
    st.sidebar.write("Harcamalarınız hakkında yapay zekaya sorular sorun.")
    
    df_expenses_sidebar = get_user_expenses(st.session_state.username)
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for message in st.session_state.chat_messages:
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.sidebar.chat_input("Asistana bir şeyler sorun...")
    
    if user_question:
        st.session_state.chat_messages.append({"role": "user", "content": user_question})
        with st.sidebar.chat_message("user"):
            st.markdown(user_question)

        if client and GEMINI_API_KEY != "BURAYA_GEMINI_API_KEY_GIRINIZ":
            if not df_expenses_sidebar.empty:
                with st.sidebar.spinner("Yapay zeka verilerinizi inceliyor..."):
                    data_summary = df_expenses_sidebar.to_string(index=False)
                    chat_prompt = f"""
                    Sen kurumsal bir finansal asistansın. Aşağıda kullanıcının masraf veritabanı tablosu bulunmaktadır:
                    {data_summary}
                    
                    Kullanıcının sorusu: "{user_question}"
                    Lütfen bu verilere dayanarak Türkçe, kibar ve net bir şekilde yanıt ver.
                    """
                    chat_response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=chat_prompt
                    )
                    ai_reply = chat_response.text
                    st.session_state.chat_messages.append({"role": "assistant", "content": ai_reply})
                    with st.sidebar.chat_message("assistant"):
                        st.markdown(ai_reply)
            else:
                warning_msg = "Soru sorabilmek için veritabanınızda kayıtlı masraf olmalıdır."
                st.session_state.chat_messages.append({"role": "assistant", "content": warning_msg})
                with st.sidebar.chat_message("assistant"):
                    st.markdown(warning_msg)
        else:
            error_msg = "Geçerli bir Gemini API anahtarı gereklidir."
            st.sidebar.markdown(error_msg)

    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.chat_messages = []
        st.rerun()

    st.title("🧾 Kurumsal Masraf Otomasyonu ve AI Asistanı")
    st.markdown(f"**Hoş Geldiniz, Sn. {st.session_state.username}**. Çoklu para birimi algılama ve akıllı finansal asistan özellikleriyle donatılmış paneldesiniz.")
    st.markdown("---")

    # Bölüm 1: Fiş Yükleme ve Çoklu Para Birimi Analizi
    with st.container():
        st.subheader("📤 Fiş Yükleme ve Çoklu Para Birimi / Akıllı Analiz")
        uploaded_file = st.file_uploader("Lütfen bir fiş veya fatura görseli seçin (.png, .jpg)", type=["png", "jpg", "jpeg"])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Yüklenen Fiş Görseli", width=320)
            
            status_placeholder = st.empty()
            status_placeholder.info("🔄 Fiş taranıyor, döviz kurları kontrol ediliyor ve Gemini AI analiz yapıyor...")
            
            try:
                extracted_text = pytesseract.image_to_string(image, lang='tur+eng')
                
                ai_date = ""
                ai_amount = ""
                ai_category = "Genel / Diğer"
                detected_currency = "TL"
                
                if client and GEMINI_API_KEY != "BURAYA_GEMINI_API_KEY_GIRINIZ":
                    prompt = """
                    Bu fiş görselini analiz et ve bana tam olarak şu formatta bilgi ver:
                    Tarih: DD.MM.YYYY (Bulamazsan bugünün tarihini ver)
                    Tutar: Sadece sayısal değer (Örn: 150.50)
                    ParaBirimi: [TL, USD, EUR, GBP] (Fişte geçen para birimini seç)
                    Kategori: Şu seçeneklerden biri olmalı -> [Ulaşım, Yemek / Gıda, Teknoloji / Ofis, Genel / Diğer]
                    Lütfen başka hiçbir açıklama yazma, sadece bu 4 satırı ver.
                    """
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[image, prompt]
                    )
                    ai_response_text = response.text
                    
                    date_match = re.search(r"Tarih:\s*([0-9]{2}[./-][0-9]{2}[./-][0-9]{4})", ai_response_text)
                    amount_match = re.search(r"Tutar:\s*([0-9]+[.,][0-9]{2})", ai_response_text)
                    curr_match = re.search(r"ParaBirimi:\s*(.*)", ai_response_text)
                    cat_match = re.search(r"Kategori:\s*(.*)", ai_response_text)
                    
                    if date_match: ai_date = date_match.group(1).replace("-", ".")
                    if amount_match: ai_amount = amount_match.group(1).replace(",", ".")
                    if curr_match: detected_currency = curr_match.group(1).strip()
                    if cat_match: 
                        clean_cat = cat_match.group(1).strip()
                        if clean_cat in ["Ulaşım", "Yemek / Gıda", "Teknoloji / Ofis", "Genel / Diğer"]:
                            ai_category = clean_cat

                if not ai_amount:
                    amount_patterns = r"([0-9]+[.,][0-9]{2})"
                    matches = re.findall(amount_patterns, extracted_text)
                    ai_amount = matches[-1].replace(",", ".") if matches else "0.00"
                    
                if not ai_date:
                    date_pattern = r"([0-9]{2}[./-][0-9]{2}[./-][0-9]{4})"
                    date_matches = re.findall(date_pattern, extracted_text)
                    ai_date = date_matches[0] if date_matches else datetime.now().strftime("%d.%m.%Y")

                # Döviz Çevirici Simülasyonu
                numeric_amount = float(ai_amount)
                exchange_info = ""
                if detected_currency == "USD":
                    numeric_amount = numeric_amount * 35.0
                    exchange_info = " (Algılanan: 1 USD = 35.00 TL kuru ile çevrildi)"
                elif detected_currency == "EUR":
                    numeric_amount = numeric_amount * 38.0
                    exchange_info = " (Algılanan: 1 EUR = 38.00 TL kuru ile çevrildi)"
                elif detected_currency == "GBP":
                    numeric_amount = numeric_amount * 45.0
                    exchange_info = " (Algılanan: 1 GBP = 45.00 TL kuru ile çevrildi)"

                status_placeholder.success(f"✅ Fiş analiz edildi! Para Birimi: {detected_currency}{exchange_info}")

                col1, col2, col3 = st.columns(3)
                col1.metric("Fiş Tarihi", ai_date)
                col2.metric("TL Karşılığı Tutar", f"{numeric_amount:.2f} TL")
                
                category_options = ["Genel / Diğer", "Ulaşım", "Yemek / Gıda", "Teknoloji / Ofis"]
                default_index = category_options.index(ai_category) if ai_category in category_options else 0
                
                category = col3.selectbox("Masraf Kategorisi", category_options, index=default_index)

                if st.button("💾 Bu Masrafı Kalıcı Olarak Kaydet", use_container_width=True):
                    add_expense(st.session_state.username, ai_date, numeric_amount, category, extracted_text)
                    st.success("Masraf hesabınıza başarıyla kaydedildi!")
                    st.rerun()

                with st.expander("🔍 Fişten Okunan Ham Metin ve Yapay Zeka Çıktısı"):
                    st.text(extracted_text)
                    
            except Exception as e:
                status_placeholder.error(f"İşlem sırasında bir hata oluştu: {e}")

    st.markdown("---")

    # Bölüm 2: Veritabanı ve Tablolar
    with st.container():
        st.subheader("📊 Masraf Veritabanı ve Raporlama Paneli")

        df_expenses = get_user_expenses(st.session_state.username)

        if not df_expenses.empty:
            with st.expander("🔍 Gelişmiş Filtreleme ve Tarih Aralığı Seçenekleri"):
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    selected_category = st.selectbox("Kategoriye Göre Filtrele", ["Tümü"] + list(df_expenses["Kategori"].unique()))
                    if selected_category != "Tümü":
                        df_expenses = df_expenses[df_expenses["Kategori"] == selected_category]
                
                with col_f2:
                    enable_date_filter = st.checkbox("Tarih Aralığı Filtresi Uygula")
                    if enable_date_filter:
                        temp_dates = pd.to_datetime(df_expenses["Tarih"], format="%d.%m.%Y", errors="coerce")
                        min_d = temp_dates.min().date() if not temp_dates.isna().all() else date.today()
                        max_d = temp_dates.max().date() if not temp_dates.isna().all() else date.today()
                        
                        start_date = st.date_input("Başlangıç Tarihi", min_d)
                        end_date = st.date_input("Bitiş Tarihi", max_d)
                        
                        mask = (temp_dates.dt.date >= start_date) & (temp_dates.dt.date <= end_date)
                        df_expenses = df_expenses[mask]

            st.dataframe(df_expenses, use_container_width=True)
            
            total_spent = df_expenses["Tutar (TL)"].sum()
            st.metric("Filtrelenen Toplam Harcama", f"{total_spent:,.2f} TL")
            
            st.subheader("📈 Kategori Bazlı Harcama Dağılımı")
            if not df_expenses.empty:
                category_grouped = df_expenses.groupby("Kategori")["Tutar (TL)"].sum()
                st.bar_chart(category_grouped)

            st.markdown("---")
            col_act1, col_act2 = st.columns(2)
            
            with col_act1:
                csv_data = df_expenses.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(
                    label="📥 Masraf Raporunu Excel/CSV Olarak İndir",
                    data=csv_data,
                    file_name=f"{st.session_state.username}_masraf_raporu.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            with col_act2:
                manager_email = st.text_input("Yönetici E-Posta Adresi", value="yonetici@sirket.com")
                if st.button("📤 Yöneticiye Rapor Gönder (E-Posta Simülasyonu)", use_container_width=True):
                    st.success(f"Başarılı! Güncel rapor ({manager_email}) adresine iletildi.")

            st.markdown("---")
            if st.button("🗑️ Veritabanımı Tamamen Temizle"):
                clear_user_db(st.session_state.username)
                st.success("Kişisel veritabanınız sıfırlandı!")
                st.rerun()
        else:
            st.info("Veritabanınızda henüz kayıtlı bir masraf bulunmuyor. Yukarıdan fiş yükleyip eklemeye başlayabilirsiniz.")