import streamlit as st
import json
import os
import re
import jwt
import bcrypt
import datetime
import smtplib
import random
from email.message import EmailMessage

# ---------------- SECRETS ---------------- #
JWT_SECRET = os.environ.get("JWT_SECRET")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

if not JWT_SECRET or not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    st.error("Missing required secrets (JWT_SECRET / EMAIL_ADDRESS / EMAIL_PASSWORD). "
             "Set them as environment variables before running the app.")
    st.stop()

USERS_FILE = "users.json"
OTP_EXPIRY_MINUTES = 5

PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
EMAIL_REGEX = r'^[A-Za-z0-9._%+-]{2,}@[A-Za-z]{2,}\.[A-Za-z]{2,}$'


# ---------------- DATA HELPERS ---------------- #
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def hash_txt(t):
    return bcrypt.hashpw(t.encode(), bcrypt.gensalt()).decode()


def check_txt(t, h):
    try:
        return bcrypt.checkpw(t.encode(), h.encode())
    except (ValueError, AttributeError):
        return False


def make_otp_token(email, otp):
    payload = {
        "sub": email,
        "otp_hash": hash_txt(otp),
        "type": "password_reset_otp",
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_otp_token(token, input_otp, email):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("sub") != email or payload.get("type") != "password_reset_otp":
            return False, "Security token mismatch."
        if check_txt(input_otp, payload["otp_hash"]):
            return True, "Valid"
        return False, "Invalid 6-digit OTP code."
    except jwt.ExpiredSignatureError:
        return False, f"This OTP expired after {OTP_EXPIRY_MINUTES} minutes. Please request a new one."
    except jwt.InvalidTokenError:
        return False, "Invalid or corrupted verification token."


def send_otp_email(receiver_email, otp):
    msg = EmailMessage()
    msg["Subject"] = "Your OTP for Password Reset"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email
    msg.set_content(
        f"Your OTP is: {otp}\nThis code expires in {OTP_EXPIRY_MINUTES} minutes.\n"
        f"If you did not request this, you can safely ignore this email."
    )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


# ---------------- PAGE SETUP ---------------- #
st.set_page_config(page_title="Infosys FranchiseOps AI", page_icon="🏢", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

    .stApp {
        background: radial-gradient(circle at top, #eef1fb 0%, #e4e8f7 45%, #dfe4f5 100%);
    }
    div.block-container {
        max-width: 480px;
        padding-top: 2.8rem;
    }

    .brand-badge {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 0.3rem;
    }
    .brand-badge .logo-box {
        background: linear-gradient(135deg, #4f46e5, #6366f1);
        color: white;
        font-family: 'Poppins', sans-serif;
        font-weight: 800;
        font-size: 1.1rem;
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
    }
    .brand-badge h1 {
        font-family: 'Poppins', sans-serif !important;
        font-size: 1.7rem !important;
        font-weight: 800 !important;
        color: #1a1f36;
        margin: 0 !important;
        letter-spacing: -0.5px;
    }
    .brand-sub {
        text-align: center;
        color: #6b7280;
        font-size: 0.85rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 0.98rem;
        margin-bottom: 2rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border-radius: 20px !important;
        box-shadow: 0 12px 40px rgba(79, 70, 229, 0.12), 0 2px 8px rgba(31, 41, 55, 0.06);
        border: 1px solid #eef0f4 !important;
        padding: 0.8rem 0.6rem !important;
    }

    h3 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        color: #1a1f36 !important;
        font-size: 1.45rem !important;
        margin-bottom: 1rem !important;
    }

    .stTextInput label p {
        font-weight: 600 !important;
        color: #374151 !important;
        font-size: 0.88rem !important;
    }
    .stTextInput input {
        border-radius: 10px !important;
        border: 1.5px solid #e2e5ee !important;
        padding: 0.7rem 0.9rem !important;
        font-size: 1rem !important;
        background-color: #fafbff !important;
    }
    .stTextInput input:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12) !important;
    }

    button[kind="primary"] {
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 0.9rem 0 !important;
        min-height: 3.2rem !important;
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        color: white !important;
        border: none !important;
        margin-top: 0.8rem !important;
        box-shadow: 0 6px 18px rgba(79, 70, 229, 0.35) !important;
        transition: all 0.15s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 22px rgba(79, 70, 229, 0.45) !important;
        background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%) !important;
    }

    button[kind="secondary"] {
        background: none !important;
        box-shadow: none !important;
        border: none !important;
        color: #4f46e5 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.4rem 0 !important;
        min-height: auto !important;
        margin-top: 0.5rem !important;
        text-decoration: underline;
    }
    button[kind="secondary"]:hover {
        color: #3730a3 !important;
        background: none !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f36 0%, #12162a 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #f3f4f6 !important;
    }
    section[data-testid="stSidebar"] label {
        font-weight: 500 !important;
    }
    .sidebar-footer {
        position: fixed;
        bottom: 1.4rem;
        left: 1.4rem;
        color: #6b7280;
        font-size: 0.72rem;
    }
    .milestone-banner {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 0.85rem 1.1rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.95rem;
        text-align: center;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 0.6rem 0;
        border-bottom: 1px solid #f0f1f5;
        font-size: 0.92rem;
    }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #6b7280; font-weight: 500; }
    .info-value { color: #1a1f36; font-weight: 600; }
    .coming-soon {
        background: #f9fafb;
        border: 1px dashed #d1d5db;
        border-radius: 10px;
        padding: 0.9rem;
        text-align: center;
        color: #6b7280;
        font-size: 0.88rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Login"
if "auth_view" not in st.session_state:
    st.session_state["auth_view"] = "login"
if "forgot_stage" not in st.session_state:
    st.session_state["forgot_stage"] = "choose"
if "dashboard_view" not in st.session_state:
    st.session_state["dashboard_view"] = "Home"


# ---------------- DASHBOARD (only if a VALID JWT exists) ---------------- #
if "token" in st.session_state:
    try:
        payload = jwt.decode(st.session_state["token"], JWT_SECRET, algorithms=["HS256"])

        # ---- Dashboard sidebar menu ---- #
        st.sidebar.markdown("""
        <div style="padding: 0.3rem 0 1.4rem;">
            <div style="display:flex;align-items:center;gap:8px;">
                <div style="background:linear-gradient(135deg,#4f46e5,#6366f1);width:32px;height:32px;
                            border-radius:9px;display:flex;align-items:center;justify-content:center;
                            font-family:'Poppins',sans-serif;font-weight:800;font-size:0.85rem;color:white;">IN</div>
                <div style="font-family:'Poppins',sans-serif;font-weight:700;font-size:1rem;color:#f3f4f6;">FranchiseOps AI</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.markdown(
            '<div style="color:#9ca3af;font-size:0.72rem;font-weight:700;letter-spacing:1px;'
            'text-transform:uppercase;margin-bottom:0.4rem;">Dashboard</div>',
            unsafe_allow_html=True
        )

        dash_pages = ["Home", "My Profile"]
        dash_labels = {"Home": "🏠  Home", "My Profile": "👤  My Profile"}

        dashboard_view = st.sidebar.radio(
            "Dashboard Nav",
            dash_pages,
            index=dash_pages.index(st.session_state["dashboard_view"]),
            label_visibility="collapsed",
            format_func=lambda p: dash_labels[p]
        )
        st.session_state["dashboard_view"] = dashboard_view

        st.sidebar.markdown('<hr style="border-color:#2d3350;margin:1rem 0 0.8rem;">', unsafe_allow_html=True)
        if st.sidebar.button("Log Out", type="primary", use_container_width=True, icon="🔒"):
            del st.session_state["token"]
            del st.session_state["username"]
            st.session_state["active_page"] = "Login"
            st.session_state["auth_view"] = "login"
            st.session_state["dashboard_view"] = "Home"
            st.rerun()

        st.sidebar.markdown(
            '<div class="sidebar-footer">🟢 System Online &nbsp;·&nbsp; v1.0</div>',
            unsafe_allow_html=True
        )

        # ---- Main dashboard content ---- #
        st.markdown("""
        <div class="brand-badge">
            <div class="logo-box">IN</div>
            <h1>FranchiseOps AI</h1>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="brand-sub">Infosys Springboard</div>', unsafe_allow_html=True)

        users = load_users()
        current_user = next((u for u in users if u["username"] == st.session_state["username"]), None)

        if dashboard_view == "Home":
            st.markdown(
                '<div class="milestone-banner">🎉 Welcome! Milestone 1 Complete — '
                'Authentication System is Live</div>',
                unsafe_allow_html=True
            )

            with st.container(border=True):
                st.subheader(f"Welcome back, {st.session_state['username']} 👋")
                st.write("You're securely logged in with an active JWT session.")

                st.markdown('<div class="coming-soon">🚧 Franchise management features coming in the next milestone.</div>',
                            unsafe_allow_html=True)

        elif dashboard_view == "My Profile":
            with st.container(border=True):
                st.subheader("My Profile")

                if current_user:
                    st.markdown(f"""
                        <div class="info-row"><span class="info-label">Username</span><span class="info-value">{current_user['username']}</span></div>
                        <div class="info-row"><span class="info-label">Email</span><span class="info-value">{current_user['email']}</span></div>
                        <div class="info-row"><span class="info-label">Security Question</span><span class="info-value">{current_user['security_question']}</span></div>
                        <div class="info-row"><span class="info-label">Account Status</span><span class="info-value">🟢 Active</span></div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("Profile data not found.")

        st.stop()

    except jwt.ExpiredSignatureError:
        st.warning("Your session has expired. Please log in again.")
        del st.session_state["token"]
        del st.session_state["username"]

    except jwt.InvalidTokenError:
        st.error("Invalid session token. Please log in again.")
        del st.session_state["token"]
        del st.session_state["username"]

st.markdown("""
<div class="brand-badge">
    <div class="logo-box">IN</div>
    <h1>FranchiseOps AI</h1>
</div>
""", unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Infosys Springboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">User Authentication System</div>', unsafe_allow_html=True)

# ---------------- SIDEBAR NAV (pre-login) ---------------- #
st.sidebar.markdown("""
<div style="padding: 0.3rem 0 1.4rem;">
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="background:linear-gradient(135deg,#4f46e5,#6366f1);width:32px;height:32px;
                    border-radius:9px;display:flex;align-items:center;justify-content:center;
                    font-family:'Poppins',sans-serif;font-weight:800;font-size:0.85rem;color:white;">IN</div>
        <div style="font-family:'Poppins',sans-serif;font-weight:700;font-size:1rem;color:#f3f4f6;">FranchiseOps AI</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    '<div style="color:#9ca3af;font-size:0.72rem;font-weight:700;letter-spacing:1px;'
    'text-transform:uppercase;margin-bottom:0.4rem;">Account</div>',
    unsafe_allow_html=True
)

pages = ["Login", "Signup", "Admin Login"]
labels = {"Login": "🔑  Login", "Signup": "✍️  Signup", "Admin Login": "🛡️  Admin Login"}

menu = st.sidebar.radio(
    "Navigation",
    pages,
    index=pages.index(st.session_state["active_page"]) if st.session_state["active_page"] in pages else 0,
    label_visibility="collapsed",
    format_func=lambda p: labels[p]
)
st.session_state["active_page"] = menu
if menu != "Login":
    st.session_state["auth_view"] = "login"

st.sidebar.markdown(
    '<div class="sidebar-footer">🟢 System Online &nbsp;·&nbsp; v1.0</div>',
    unsafe_allow_html=True
)

# ---------------- LOGIN + FORGOT PASSWORD ---------------- #
if menu == "Login":

    if st.session_state["auth_view"] == "login":
        with st.container(border=True):
            st.subheader("Welcome back")

            username = st.text_input("Username / Email")
            password = st.text_input("Password", type="password")

            if st.button("Login", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("Please fill all fields.")
                else:
                    users = load_users()
                    found = False

                    for user in users:
                        if (user["username"] == username or user["email"] == username) \
                                and check_txt(password, user["password"]):
                            found = True
                            payload = {
                                "username": user["username"],
                                "email": user["email"],
                                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                            }
                            token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
                            st.session_state["token"] = token
                            st.session_state["username"] = user["username"]
                            st.session_state["dashboard_view"] = "Home"
                            st.success("Login Successful!")
                            st.rerun()

                    if not found:
                        st.error("Invalid Username or Password")

            if st.button("Forgot Password?", type="secondary", use_container_width=True):
                st.session_state["auth_view"] = "forgot"
                st.session_state["forgot_stage"] = "choose"
                st.rerun()

            st.markdown(
                '<div style="text-align:center;color:#6b7280;font-size:0.85rem;margin-top:0.7rem;">'
                'Not registered yet?</div>',
                unsafe_allow_html=True
            )
            if st.button("Create an account →", type="secondary", use_container_width=True):
                st.session_state["active_page"] = "Signup"
                st.rerun()

    else:
        with st.container(border=True):
            st.subheader("Reset your password")

            option = st.radio("Choose Recovery Method", ["Security Question", "OTP via Email"])

            if option == "Security Question":
                username = st.text_input("Username")

                if username:
                    users = load_users()
                    current_user = next((u for u in users if u["username"] == username), None)

                    if current_user:
                        st.info(current_user["security_question"])

                        answer = st.text_input("Security Answer")
                        new_password = st.text_input("New Password", type="password")
                        confirm_password = st.text_input("Confirm Password", type="password")

                        if st.button("Reset Password", type="primary", use_container_width=True):
                            if answer != current_user["security_answer"]:
                                st.error("Incorrect security answer.")
                            elif new_password != confirm_password:
                                st.error("Passwords do not match.")
                            elif not re.match(PASSWORD_REGEX, new_password):
                                st.error("Password must contain uppercase, lowercase, number and special symbol.")
                            else:
                                current_user["password"] = hash_txt(new_password)
                                save_users(users)
                                st.success("Password updated successfully! Redirecting to Login...")
                                st.session_state["auth_view"] = "login"
                                st.rerun()
                    else:
                        st.error("Username not found.")

            else:
                if st.session_state["forgot_stage"] == "choose":
                    email = st.text_input("Registered Email")

                    if st.button("Send OTP", type="primary", use_container_width=True):
                        users = load_users()
                        registered = any(u["email"] == email for u in users)

                        if not registered:
                            st.error("Email not registered.")
                        else:
                            otp = f"{random.randint(100000, 999999)}"
                            try:
                                send_otp_email(email, otp)
                                st.session_state["otp_token"] = make_otp_token(email, otp)
                                st.session_state["reset_email"] = email
                                st.session_state["forgot_stage"] = "otp_sent"
                                st.success("OTP sent successfully! Check your inbox.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to send OTP: {e}")

                elif st.session_state["forgot_stage"] == "otp_sent":
                    st.info(f"Code sent to **{st.session_state['reset_email']}** "
                            f"(valid for {OTP_EXPIRY_MINUTES} minutes).")

                    entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6)
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")

                    c1, c2 = st.columns(2)

                    with c1:
                        if st.button("Verify & Reset", type="primary", use_container_width=True):
                            if not entered_otp or len(entered_otp) != 6:
                                st.error("Please enter the valid 6-digit code.")
                            elif new_password != confirm_password:
                                st.error("Passwords do not match.")
                            elif not re.match(PASSWORD_REGEX, new_password):
                                st.error("Password must contain uppercase, lowercase, number and special symbol.")
                            else:
                                ok, msg = verify_otp_token(
                                    st.session_state["otp_token"], entered_otp, st.session_state["reset_email"]
                                )
                                if not ok:
                                    st.error(msg)
                                else:
                                    users = load_users()
                                    for user in users:
                                        if user["email"] == st.session_state["reset_email"]:
                                            user["password"] = hash_txt(new_password)
                                            break
                                    save_users(users)

                                    del st.session_state["otp_token"]
                                    del st.session_state["reset_email"]
                                    st.session_state["forgot_stage"] = "choose"
                                    st.success("Password updated successfully! Redirecting to Login...")
                                    st.session_state["auth_view"] = "login"
                                    st.rerun()

                    with c2:
                        if st.button("Start Over", type="secondary", use_container_width=True):
                            st.session_state["forgot_stage"] = "choose"
                            st.rerun()

            if st.button("← Back to Login", type="secondary", use_container_width=True):
                st.session_state["auth_view"] = "login"
                st.session_state["forgot_stage"] = "choose"
                st.rerun()

# ---------------- SIGNUP ---------------- #
elif menu == "Signup":
    with st.container(border=True):
        st.subheader("Create your account")

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        question = st.selectbox(
            "Security Question",
            [
                "What is your pet's name?",
                "What is your favourite colour?",
                "What is your birthplace?",
                "What is your mother's maiden name?"
            ]
        )
        answer = st.text_input("Security Answer")

        if st.button("Create Account", type="primary", use_container_width=True):
            if not all([username, email, password, confirm_password, answer]):
                st.error("Please fill all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif not re.match(EMAIL_REGEX, email):
                st.error("Enter a valid email address.")
            elif not re.match(PASSWORD_REGEX, password):
                st.error("Password must be at least 8 characters and contain uppercase, lowercase, number and special symbol.")
            else:
                users = load_users()

                if any(u["username"] == username for u in users):
                    st.error("Username already exists.")
                else:
                    users.append({
                        "username": username,
                        "email": email,
                        "password": hash_txt(password),
                        "security_question": question,
                        "security_answer": answer
                    })
                    save_users(users)
                    st.success("Account created successfully! Redirecting to Login...")
                    st.session_state["active_page"] = "Login"
                    st.session_state["auth_view"] = "login"
                    st.rerun()

        st.markdown(
            '<div style="text-align:center;color:#6b7280;font-size:0.85rem;margin-top:0.7rem;">'
            'Already have an account?</div>',
            unsafe_allow_html=True
        )
        if st.button("Back to Login →", type="secondary", use_container_width=True):
            st.session_state["active_page"] = "Login"
            st.rerun()

# ---------------- ADMIN ---------------- #
elif menu == "Admin Login":
    with st.container(border=True):
        st.subheader("Admin Access")

        if "admin_logged_in" not in st.session_state:
            st.session_state["admin_logged_in"] = False

        if not st.session_state["admin_logged_in"]:
            admin = st.text_input("Admin Username")
            password = st.text_input("Admin Password", type="password")

            if st.button("Admin Login", type="primary", use_container_width=True):
                if admin == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else:
                    st.error("Invalid admin credentials.")
        else:
            st.write("👥 **Registered Users**")
            users = load_users()

            if users:
                st.table([{"Username": u["username"], "Email": u["email"]} for u in users])
            else:
                st.info("No registered users yet.")

            if st.button("Admin Logout", type="primary", use_container_width=True):
                st.session_state["admin_logged_in"] = False
                st.rerun()
