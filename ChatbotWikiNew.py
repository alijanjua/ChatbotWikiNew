import streamlit as st
import requests
import wikipedia

# Firebase API Key from secrets
FIREBASE_API_KEY = st.secrets["firebase"]["apiKey"]

# Initialize session state
if "user" not in st.session_state:
    st.session_state.user = None
if "query_history" not in st.session_state:
    st.session_state.query_history = {}

# Firebase REST API functions
def signup_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

def login_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload).json()

# Auth UI
def login_or_signup():
    st.title("🔐 Chatbot-Wiki Login")
    mode = st.radio("Select Mode", ["Login", "Sign Up"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if mode == "Login":
        if st.button("Login"):
            result = login_user(email, password)
            if "idToken" in result:
                st.session_state.user = result
                st.success("✅ Logged in!")
                st.rerun()
            else:
                st.error("❌ Login failed")
                st.write(result)
    elif mode == "Sign Up":
        if st.button("Create Account"):
            result = signup_user(email, password)
            if "idToken" in result:
                st.success("🎉 Account created! Please login.")
            else:
                st.error("❌ Signup failed")
                st.write(result)

# Main App
def main_app():
    st.sidebar.success(f"Logged in as: {st.session_state.user['email']}")
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    user_email = st.session_state.user["email"]
    if user_email not in st.session_state.query_history:
        st.session_state.query_history[user_email] = []

    user_history = st.session_state.query_history[user_email]

    st.title("📚 Chatbot-Wiki")
    user_input = st.text_input("🔍 Ask Wikipedia:")

    if st.button("Get Answer"):
        try:
            summary = wikipedia.summary(user_input, sentences=3)
            st.success("✅ Answer:")
            st.write(summary)

            if user_input and user_input not in user_history:
                user_history.insert(0, user_input)
                st.session_state.query_history[user_email] = user_history[:5]
        except:
            st.warning("⚠️ Could not retrieve this query.")

    # Recent Queries
    st.markdown("### 🕘 Your Recent Queries")
    for idx, query in enumerate(user_history, 1):
        if st.button(f"{idx}. {query}", key=f"query_{idx}_{query}"):
            try:
                summary = wikipedia.summary(query, sentences=3)
                st.markdown(f"**📖 {query}**")
                st.write(summary)
            except:
                st.warning("Could not retrieve this query.")

# Routing
if st.session_state.user:
    main_app()
else:
    login_or_signup()
