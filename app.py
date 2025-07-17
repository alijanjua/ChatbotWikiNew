
import streamlit as st
import requests
import wikipedia
import datetime
from google.cloud import firestore
from reportlab.pdfgen import canvas
from io import BytesIO

# Page config
st.set_page_config(page_title="Chatbot-Wiki", layout="wide")

# Firebase secrets
API_KEY = st.secrets["firebase"]["apiKey"]
PROJECT_ID = st.secrets["firebase"]["projectId"]

# Firestore setup
db = firestore.Client(project=PROJECT_ID)

# Helper functions
def sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}).json()

def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    return requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}).json()

def reset_password(email):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"
    return requests.post(url, json={"requestType": "PASSWORD_RESET", "email": email}).json()

def verify_email(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"
    return requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token}).json()

def save_query(email, query):
    doc_ref = db.collection("queries").document(email).collection("history").document()
    doc_ref.set({"query": query, "timestamp": datetime.datetime.now()})

def get_user_queries(email):
    docs = db.collection("queries").document(email).collection("history").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()
    return [{"query": doc.to_dict()["query"], "timestamp": doc.to_dict()["timestamp"]} for doc in docs]

def export_pdf(queries):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 12)
    p.drawString(100, 800, "Chatbot-Wiki - Query History")
    y = 780
    for item in queries:
        p.drawString(100, y, f"{item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {item['query']}")
        y -= 20
    p.save()
    buffer.seek(0)
    return buffer

# Main interface
if "user" not in st.session_state:
    st.session_state.user = None

def auth_ui():
    st.title("🔐 Chatbot-Wiki Authentication")
    mode = st.radio("Choose Action", ["Login", "Sign Up", "Reset Password"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password") if mode != "Reset Password" else ""

    if st.button(mode):
        if mode == "Login":
            res = login(email, password)
            if "idToken" in res:
                st.session_state.user = {"email": email, "idToken": res["idToken"]}
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Login failed")
        elif mode == "Sign Up":
            res = sign_up(email, password)
            if "idToken" in res:
                verify_email(res["idToken"])
                st.success("Signed up! Please verify your email.")
            else:
                st.error("Signup failed")
        elif mode == "Reset Password":
            res = reset_password(email)
            if "email" in res:
                st.success("Password reset email sent.")
            else:
                st.error("Failed to send reset email")

def app_ui():
    st.sidebar.image("chatbotwiki_logo.png", width=120)
    menu = st.sidebar.radio("Navigate", ["Home", "Dashboard", "About", "Contact Us"])
    st.sidebar.markdown(f"**User:** {st.session_state.user['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    st.title("📚 Chatbot-Wiki")

    if menu == "Home":
        query = st.text_input("Ask something...")
        if st.button("Search"):
            try:
                answer = wikipedia.summary(query, sentences=3)
                st.success("Answer:")
                st.write(answer)
                save_query(st.session_state.user["email"], query)
            except:
                st.warning("Could not fetch answer.")

        st.markdown("### Recent Queries")
        recent = get_user_queries(st.session_state.user["email"])
        for item in recent:
            st.write(f"🕒 {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} — {item['query']}")

        if st.button("📥 Export to PDF"):
            pdf = export_pdf(recent)
            st.download_button("Download PDF", data=pdf, file_name="query_history.pdf")

    elif menu == "Dashboard":
        queries = get_user_queries(st.session_state.user["email"])
        st.metric("Total Recent Queries", len(queries))
        if queries:
            st.write("Most Recent Query:")
            st.info(queries[0]["query"])

    elif menu == "About":
        st.markdown("This application will take a user input and get the query from Wikipedia website to respond to that query. It is a fully functional app with enhanced feature set incorporated into it.")

    elif menu == "Contact Us":
        st.markdown("📧 Email: support@chatbotwiki.com\n🌐 Website: https://chatbotwiki.app")

# Run the appropriate UI
if st.session_state.user:
    app_ui()
else:
    auth_ui()
