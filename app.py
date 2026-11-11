import streamlit as st
from pypdf import PdfReader
from PIL import Image
import io
import os
import time
from groq import Groq
from langchain_groq import ChatGroq

# 1. Ρύθμιση Tesseract OCR στα Windows
import pytesseract

tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

# 2. Ρύθμιση Σελίδας & Σκούρου UI για τα Uploaders
st.set_page_config(page_title="StudyBot AI", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    div[data-testid="stFileUploader"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        background-color: rgba(0, 0, 0, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    .telemetry-card {
        background-color: rgba(255, 255, 255, 0.03);
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 3px solid #4CAF50;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 StudyBot – AI Assistant Σημειώσεων & Εξετάσεων")
st.write("Ανέβασε το υλικό μελέτης σου (σημειώσεις, διαφάνειες, θέματα) για αυτόματη ανάλυση!")

# 3. Sidebar για API Key & LLM Telemetry
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις & AI Telemetry")
    default_key = st.secrets.get("GROQ_API_KEY", "")
    api_key = st.text_input(
        "Groq API Key", 
        value=default_key, 
        type="password", 
        help="Φορτώνεται αυτόματα αν υπάρχει στο secrets.toml"
    )
    
    if api_key:
        st.markdown('<div class="telemetry-card"><b>🟢 API Status:</b> Ενεργό<br><small>Dynamic LLM Routing Enabled</small></div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Παρακαλώ εισάγετε API Key")

    # Telemetry Stats
    if "last_latency" in st.session_state:
        st.metric("⚡ Χρόνος Απόκρισης LLM", f"{st.session_state.last_latency:.2f} sec")
        
    st.markdown("---")
    if st.button("🗑️ Καθαρισμός Ιστορικού Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Συνάρτηση επεξεργασίας οποιουδήποτε τύπου αρχείου
def process_files(files):
    extracted_text = ""
    pages_count = 0
    images_list = []
    
    for file in files:
        file_name = file.name.lower()
        if file_name.endswith('.pdf'):
            try:
                reader = PdfReader(file)
                pages_count += len(reader.pages)
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        extracted_text += txt + "\n"
            except Exception as e:
                st.warning(f"Σφάλμα ανάγνωσης αρχείου {file.name}: {e}")
        elif file_name.endswith(('.jpg', '.jpeg', '.png')):
            try:
                img = Image.open(file)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images_list.append((file.name, img))
                
                ocr_out = pytesseract.image_to_string(img, lang="ell+eng")
                if ocr_out.strip():
                    extracted_text += f"\n--- Κείμενο Εικόνας ({file.name}) ---\n" + ocr_out
            except Exception as e:
                st.warning(f"Σφάλμα ανάγνωσης εικόνας {file.name}: {e}")
                
    return extracted_text, pages_count, images_list

# 4. Φόρτωση Αρχείων
col1, col2 = st.columns(2)
supported_types = ["pdf", "jpg", "jpeg", "png"]

with col1:
    st.subheader("📚 Σημειώσεις & Διαφάνειες")
    uploaded_col1 = st.file_uploader(
        "Ανέβασε αρχεία σημειώσεων", 
        type=supported_types, 
        accept_multiple_files=True,
        key="uploader_col1"
    )
    text_col1, pages_col1, imgs_col1 = process_files(uploaded_col1) if uploaded_col1 else ("", 0, [])
    
    if uploaded_col1:
        if imgs_col1:
            cols = st.columns(min(len(imgs_col1), 3))
            for idx, (name, img) in enumerate(imgs_col1):
                with cols[idx % 3]:
                    st.image(img, caption=name, use_container_width=True)
        st.success(f"Επιτυχής φόρτωση {len(uploaded_col1)} αρχείων σημειώσεων!")

with col2:
    st.subheader("📸 Παλαιά Θέματα & Ασκήσεις")
    uploaded_col2 = st.file_uploader(
        "Ανέβασε αρχεία θεμάτων", 
        type=supported_types, 
        accept_multiple_files=True,
        key="uploader_col2"
    )
    text_col2, pages_col2, imgs_col2 = process_files(uploaded_col2) if uploaded_col2 else ("", 0, [])
    
    if uploaded_col2:
        if imgs_col2:
            cols = st.columns(min(len(imgs_col2), 3))
            for idx, (name, img) in enumerate(imgs_col2):
                with cols[idx % 3]:
                    st.image(img, caption=name, use_container_width=True)
        st.success(f"Επιτυχής φόρτωση {len(uploaded_col2)} αρχείων θεμάτων!")

total_text = text_col1 + "\n" + text_col2
total_files_count = (len(uploaded_col1) if uploaded_col1 else 0) + (len(uploaded_col2) if uploaded_col2 else 0)
total_pages = pages_col1 + pages_col2
total_images = len(imgs_col1) + len(imgs_col2)

# 5. Dashboard Metrics Bar (3 Στήλες - Χωρίς Context Usage)
if total_files_count > 0:
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Αρχεία Σημειώσεων", f"{len(uploaded_col1) if uploaded_col1 else 0} αρχεία")
    m2.metric("Αρχεία Θεμάτων", f"{len(uploaded_col2) if uploaded_col2 else 0} αρχεία")
    est_time = max(1, (total_pages * 2) + (total_images * 4) + (total_files_count * 2))
    m3.metric("Εκτιμώμενος Χρόνος Μελέτης", f"~{est_time} λεπτά")

st.markdown("---")

# 6. Κεντρική Συνάρτηση AI με Χρονομέτρηση Latency
def call_ai(prompt_text, api_key, context_text=""):
    start_time = time.time()
    client = Groq(api_key=api_key)
    
    try:
        available_models = [m.id for m in client.models.list().data]
    except Exception:
        available_models = []

    candidates = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    ]

    models_to_try = [m for m in candidates if m in available_models]
    if not models_to_try:
        models_to_try = available_models if available_models else candidates

    full_context = ""
    if context_text.strip():
        full_context += f"\n\n[Περιεχόμενο Υλικού Μελέτης]:\n{context_text[:10000]}"

    system_instruction = (
        "Είσαι ο ακαδημαϊκός βοηθός StudyBot. "
        "Απάντα ΠΑΝΤΑ με καθαρή ελληνική γλώσσα, δομημένες παραγράφους και λίστες. "
        "Χρησιμοποίησε όλο το διαθέσιμο κείμενο για να δώσεις ακριβείς απαντήσεις."
    )

    full_prompt = f"{system_instruction}\n\n{prompt_text}{full_context}"

    last_error = None
    for model_name in models_to_try:
        try:
            llm = ChatGroq(groq_api_key=api_key, model_name=model_name)
            res = llm.invoke(full_prompt)
            st.session_state.last_latency = time.time() - start_time
            return res.content
        except Exception as e:
            last_error = e
            continue

    raise Exception(f"Σφάλμα σύνδεσης: {last_error}")

# 7. Ενέργειες AI
if total_files_count > 0:
    st.header("🤖 Λειτουργίες Μελέτης AI")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Εντοπισμός SOS & Πλάνο", 
        "📝 Δημιουργία Quiz (5 Ερωτήσεις)", 
        "💬 Live Chatbot",
        "🎴 Flashcards Μελέτης"
    ])
    
    if not api_key:
        st.info("👈 Παρακαλώ εισάγετε το Groq API Key στο πλευρικό μενού για να ξεκινήσει η επεξεργασία.")
    else:
        # Tab 1: SOS Detection
        with tab1:
            if st.button("🚀 Υπολογισμός SOS Θεμάτων", key="sos_btn", type="primary"):
                with st.spinner("Το AI αναλύει το υλικό σου..."):
                    try:
                        prompt_sos = """
Ανάλυσε το διαθέσιμο υλικό και παράγαγε:
1. Τα 3 πιο πιθανά SOS θέματα/κεφάλαια που πέφτουν στις εξετάσεις Πληροφορικής.
2. Σύντομο πλάνο μελέτης 3 βημάτων.
"""
                        out = call_ai(prompt_sos, api_key, total_text)
                        
                        st.markdown("### 📊 Αναφορά SOS & Πλάνο Μελέτης")
                        st.markdown(out)
                        
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.download_button(
                                label="📥 Λήψη SOS (.txt)",
                                data=out,
                                file_name="StudyBot_SOS_Plan.txt",
                                mime="text/plain"
                            )
                        with col_d2:
                            st.download_button(
                                label="📝 Λήψη SOS (.md)",
                                data=out,
                                file_name="StudyBot_SOS_Plan.md",
                                mime="text/markdown"
                            )
                    except Exception as e:
                        st.error(f"Σφάλμα: {e}")

        # Tab 2: Quiz Generator
        with tab2:
            if st.button("🎲 Δημιουργία Test 5 Ερωτήσεων", key="quiz_btn", type="primary"):
                with st.spinner("Δημιουργία 5 ερωτήσεων quiz..."):
                    try:
                        prompt_quiz = """
Δημιούργησε 5 ερωτήσεις πολλαπλής επιλογής (με 4 επιλογές Α, Β, Γ, Δ η κάθε μία) βασισμένες στην ύλη και το διαθέσιμο υλικό. 
Για κάθε ερώτηση:
1. Δώσε την εκφώνηση και τις 4 επιλογές.
2. Στο τέλος του quiz δώσε συγκεντρωτικά τις σωστές απαντήσεις με σύντομη αιτιολόγηση.
"""
                        out = call_ai(prompt_quiz, api_key, total_text)
                        st.markdown("### 📝 Quiz 5 Ερωτήσεων Αυτοαξιολόγησης")
                        st.markdown(out)
                        
                        st.download_button(
                            label="📥 Λήψη Quiz (.txt)",
                            data=out,
                            file_name="StudyBot_Quiz.txt",
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"Σφάλμα: {e}")

        # Tab 3: Interactive Real-Time Chat
        with tab3:
            st.markdown("### 💬 Συνομιλία με το StudyBot")
            
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            if user_input := st.chat_input("Ρώτησε οτιδήποτε για το υλικό μελέτης..."):
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.write(user_input)

                with st.chat_message("assistant"):
                    with st.spinner("Σκέφτομαι..."):
                        try:
                            prompt_chat = f"Ερώτηση χρήστη: {user_input}"
                            answer = call_ai(prompt_chat, api_key, total_text)
                            st.write(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.error(f"Σφάλμα: {e}")

        # Tab 4: Interactive Flashcards
        with tab4:
            st.markdown("### 🎴 Flashcards Αυτοαξιολόγησης")
            if st.button("✨ Δημιουργία 3 Flashcards", key="flashcards_btn"):
                with st.spinner("Δημιουργία flashcards..."):
                    try:
                        prompt_fc = """
Δημιούργησε 3 σύντομες κάρτες μελέτης (Flashcards) βασισμένες στο διαθέσιμο υλικό.
Μορφή:
Ερώτηση 1: ...
Απάντηση 1: ...
Ερώτηση 2: ...
Απάντηση 2: ...
Ερώτηση 3: ...
Απάντηση 3: ...
"""
                        fc_out = call_ai(prompt_fc, api_key, total_text)
                        st.session_state.flashcards_content = fc_out
                    except Exception as e:
                        st.error(f"Σφάλμα: {e}")
            
            if "flashcards_content" in st.session_state:
                st.info(st.session_state.flashcards_content)