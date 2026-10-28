# Kurumsal Masraf Yönetimi Projesini Çalıştırma ve API Yapılandırma Rehberi

Projeyi kendi bilgisayarınızda çalıştırmak ve Gemini API anahtarınızı eklemek için sırasıyla şu adımları takip edebilirsiniz:

1. Terminali açın ve projeyi bilgisayarınıza klonlayıp klasörüne girin: `git clone https://github.com/sedaylrm/corporate-expense-dashboard.git` ve `cd corporate-expense-dashboard`

2. Projeye ait gerekli kütüphaneleri yükleyin: `pip install -r requirements.txt`

3. Proje klasöründeki ana python dosyanızı (örneğin `app.py`) VS Code ile açın, `GEMINI_API_KEY = "BURAYA_GEMINI_API_KEY_GIRINIZ"` satırını bulup kendi Google Gemini API anahtarınızı tırnak içine yazın ve dosyayı kaydedin (`Ctrl + S`)

4. Uygulamayı başlatmak için terminale şunu yazın: `py -m streamlit run app.py` 
   *(Not: Bilgisayarınızdaki Python ayarlarına göre bu komut `python -m streamlit run app.py` veya doğrudan `streamlit run app.py` şeklinde de çalışabilir. Ayrıca projedeki ana Python dosyanızın adı farklıysa `app.py` yerine kendi dosya adınızı yazmalısınız.)*
