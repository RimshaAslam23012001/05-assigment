# 📦 Streamlit for building the web interface
import streamlit as st

# 🚫 (Not used) — JSON module for reading/writing JSON data (can be removed for now)
# import json

# 🔐 For hashing the passkey securely using SHA-256
import hashlib

# ⏳ For handling time-based lockouts and timers
import time

# 🛡 For encryption and decryption using symmetric encryption (Fernet)
from cryptography.fernet import Fernet

# 🔄 For encoding the encryption key in a URL-safe format
import base64

# 🧠 Initialize session state variables if they don’t already exist
if 'failed_attempts' not in st.session_state:
    st.session_state.failed_attempts = 0
if 'stored_data' not in st.session_state:
    st.session_state.stored_data = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'
if 'last_attempt_time' not in st.session_state:
    st.session_state.last_attempt_time = 0

# 🔐 Hash the passkey using SHA-256
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).digest()

# 🔑 Generate a Fernet-compatible encryption key from passkey
def generate_key_from_passkey(passkey):
    hashed = hashlib.sha256(passkey.encode()).digest()
    return base64.urlsafe_b64encode(hashed[:32])

# 🛡 Encrypt the user data
def encrypt_data(text, passkey):
    key = generate_key_from_passkey(passkey)
    cipher = Fernet(key)
    return cipher.encrypt(text.encode()).decode()

# 🔓 Decrypt the encrypted text
def decrypt_data(encrypted_text, passkey, data_id):
    try:
        hashed_passkey = hash_passkey(passkey)
        if data_id in st.session_state.stored_data:
            key = generate_key_from_passkey(passkey)
            cipher = Fernet(key)
            decrypted_text = cipher.decrypt(encrypted_text.encode()).decode()
            st.session_state.failed_attempts = 0  # ✅ Reset on success
            return decrypted_text
        else:
            st.session_state.failed_attempts += 1
            st.session_state.last_attempt_time = time.time()
            return None
    except Exception:
        st.session_state.failed_attempts += 1
        st.session_state.last_attempt_time = time.time()
        return None

# 🆔 Generate a unique ID for each data entry
def generate_data_id():
    import uuid
    return str(uuid.uuid4())

# ♻ Reset failed attempts counter
def reset_failed_attempts():
    st.session_state.failed_attempts = 0

# 🔄 Change the current page
def change_page(page_name):
    st.session_state.current_page = page_name

# 📌 App Title
st.title("🔐 Secure Data Encryption System")

# 🧭 Sidebar Navigation
menu = ["Home", "Store Data", "Retrieve Data", "Login"]
choice = st.sidebar.selectbox("🧭 Navigation", menu, index=menu.index(st.session_state.current_page))
st.session_state.current_page = choice

# 🚫 Lockout after too many attempts
if st.session_state.failed_attempts >= 3:
    st.session_state.current_page = "Login"
    st.warning("🚫 Too many failed attempts! Please reauthenticate.")

# 🏠 Home Page
if st.session_state.current_page == "Home":
    st.subheader("🏠 Welcome to the Secure Data System")
    st.write("Use this app to **securely store and retrieve data** using a unique passkey 🔐.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Store New Data", use_container_width=True):
            change_page("Store Data")
    with col2:
        if st.button("🔍 Retrieve Data", use_container_width=True):
            change_page("Retrieve Data")

    st.info(f"📦 Currently storing {len(st.session_state.stored_data)} encrypted data entries.")

# 💾 Store Data Page
elif st.session_state.current_page == "Store Data":
    st.subheader("💾 Store Data Securely")
    user_data = st.text_area("📝 Enter Data:")
    passkey = st.text_input("🔑 Enter Passkey:", type="password")
    confirm_passkey = st.text_input("✅ Confirm Passkey:", type="password")

    if st.button("🔒 Secure & Store"):
        if user_data and passkey and confirm_passkey:
            if passkey != confirm_passkey:
                st.error("❌ Passkeys do not match!")
            else:
                data_id = generate_data_id()
                hashed_passkey = hash_passkey(passkey)
                encrypted_text = encrypt_data(user_data, passkey)

                st.session_state.stored_data[data_id] = {
                    "encrypted_text": encrypted_text,
                    "hashed_passkey": hashed_passkey
                }

                st.success("✅ Data stored successfully!")
                st.code(data_id, language='plaintext')
                st.info("💡 Save this ID! You'll need it to retrieve your data.")
        else:
            st.error("⚠ Please fill all fields!")

# 🔍 Retrieve Data Page
elif st.session_state.current_page == "Retrieve Data":
    st.subheader("🔍 Retrieve Your Data")
    attempts_remaining = 3 - st.session_state.failed_attempts
    st.info(f"🔄 Attempts remaining: {attempts_remaining}")
    
    data_id = st.text_input("🆔 Enter Data ID:")
    passkey = st.text_input("🔑 Enter Passkey:", type="password")

    if st.button("🔓 Unlock Data"):
        if data_id and passkey:
            if data_id in st.session_state.stored_data:
                encrypted_text = st.session_state.stored_data[data_id]["encrypted_text"]
                decrypted_text = decrypt_data(encrypted_text, passkey, data_id)

                if decrypted_text:
                    st.success("✅ Decryption Successful!")
                    st.markdown("### 📄 Your Decrypted Data")
                    st.code(decrypted_text, language='plaintext')
                else:
                    st.error(f"❌ Incorrect passkey! Attempts remaining: {3 - st.session_state.failed_attempts}")
            else:
                st.error("❌ Invalid Data ID!")

            if st.session_state.failed_attempts >= 3:
                st.warning("🚫 Too many failed attempts! Redirecting to Login Page...")
                st.session_state.current_page = "Login"
                st.rerun()
        else:
            st.error("⚠ Both fields are required!")

# 🔐 Login Page (after lockout)
elif st.session_state.current_page == "Login":
    st.subheader("🔐 Reauthorization Required")

    if time.time() - st.session_state.last_attempt_time < 10 and st.session_state.failed_attempts >= 3:
        remaining_time = int(10 - (time.time() - st.session_state.last_attempt_time))
        st.warning(f"⏳ Please wait {remaining_time} seconds before trying again.")
    else:
        login_pass = st.text_input("🔑 Enter Master Password:", type="password")
        if st.button("🔓 Log In"):
            if login_pass == "admin345":
                reset_failed_attempts()
                st.success("✅ Reauthorized successfully!")
                st.session_state.current_page = "Home"
                st.rerun()
            else:
                st.error("❌ Incorrect password!")

# 📝 Footer
st.markdown("_ _ _")
st.markdown("🔐 **Secure Data Encryption System** | 🧪 Educational Project")
