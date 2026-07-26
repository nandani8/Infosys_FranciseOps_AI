"""
FranchiseOps AI - auth.py
SQLite authentication with Login, Register, Forgot Password (Security Question + OTP via Email),
progressive account lockout, OTP resend cooldown, and password strength checking.
"""
import sqlite3, jwt, bcrypt, datetime, random, smtplib, streamlit as st
from email.message import EmailMessage

import config

DB_PATH = config.DB_PATH
JWT_SECRET = getattr(config, "JWT_SECRET_KEY", None) or "super-secret-franchiseops-key-2026"
EMAIL_ID = getattr(config, "EMAIL_ID", "") or ""
EMAIL_PASSWORD = getattr(config, "EMAIL_PASSWORD", "") or ""
ADMIN_EMAIL = getattr(config, "ADMIN_EMAIL", "") or "infosys@ai"
ADMIN_PASSWORD = getattr(config, "ADMIN_PASSWORD", "") or "admin@123"

from ui_theme import COLORS

OTP_EXPIRY_MINUTES = 5
LOCKOUT_RULES = {3: 300, 4: 900}  # attempts -> seconds locked (5th = permanent)


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def hash_txt(t):
    return bcrypt.hashpw(t.encode(), bcrypt.gensalt()).decode()


def check_txt(t, h):
    try:
        return bcrypt.checkpw(t.encode(), h.encode()) if h else False
    except Exception:
        return False


def make_jwt(email, username):
    return jwt.encode(
        {"email": email, "username": username,
         "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6)},
        JWT_SECRET, algorithm="HS256"
    )


def verify_jwt(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None


def make_otp_token(email, otp):
    payload = {
        "sub": email,
        "otp_hash": hash_txt(otp),
        "type": "password_reset_otp",
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
        return False, f"OTP expired after {OTP_EXPIRY_MINUTES} minutes. Please request a new one."
    except jwt.InvalidTokenError:
        return False, "Invalid or corrupted verification token."


def send_otp_email(receiver_email, otp):
    if not EMAIL_ID or not EMAIL_PASSWORD:
        st.info(f"📧 (Console fallback — no EMAIL_ID/EMAIL_PASSWORD set) OTP for {receiver_email}: **{otp}**")
        return
    msg = EmailMessage()
    msg["Subject"] = "FranchiseOps AI - Password Reset OTP"
    msg["From"] = EMAIL_ID
    msg["To"] = receiver_email
    msg.set_content(f"Your OTP is: {otp}\nThis code expires in {OTP_EXPIRY_MINUTES} minutes.")
    html_body = f"""\
    <html><body style="font-family:Arial,sans-serif;background:#f4f5f7;padding:30px;">
    <div style="max-width:480px;margin:0 auto;background:#fff;border:1px solid #d0d0d0;border-radius:6px;padding:30px;text-align:center;">
    <h2 style="color:#1a1f36;">FranchiseOps AI Portal</h2>
    <p style="color:#333;font-size:14px;">Password reset requested for <b>{receiver_email}</b>.</p>
    <div style="display:inline-block;background:#fbe36a;border:1px solid #1a1f36;border-radius:6px;
                padding:14px 28px;font-size:28px;font-weight:700;letter-spacing:6px;color:#1a1f36;">{otp}</div>
    <p style="color:#555;font-size:13px;margin-top:20px;">Expires in {OTP_EXPIRY_MINUTES} minutes.</p>
    </div></body></html>
    """
    msg.add_alternative(html_body, subtype="html")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ID, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"Failed to send OTP email: {e}")


def password_strength(pw):
    if len(pw) < 5:
        return "weak", "🔴 Weak", "Password too weak (minimum 5 characters required)."
    elif len(pw) < 10:
        return "average", "🟡 Average", "Average strength (10+ characters recommended for enterprise security)."
    else:
        return "good", "🟢 Good", "Good password strength."


@st.cache_resource
def init_auth():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            security_question TEXT,
            security_answer_hash TEXT,
            role TEXT DEFAULT 'Franchisee',
            failed_attempts INTEGER DEFAULT 0,
            lock_until TIMESTAMP DEFAULT NULL,
            account_status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        for col, ddl in [
            ("security_question", "ALTER TABLE users ADD COLUMN security_question TEXT"),
            ("security_answer_hash", "ALTER TABLE users ADD COLUMN security_answer_hash TEXT"),
            ("failed_attempts", "ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0"),
            ("lock_until", "ALTER TABLE users ADD COLUMN lock_until TIMESTAMP DEFAULT NULL"),
            ("account_status", "ALTER TABLE users ADD COLUMN account_status TEXT DEFAULT 'active'"),
        ]:
            try:
                conn.execute(ddl)
            except Exception:
                pass

        admin_email = ADMIN_EMAIL or "infosys@ai"
        admin_pw = ADMIN_PASSWORD or "admin@123"
        existing = conn.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone()
        if not existing:
            conn.execute("""INSERT OR IGNORE INTO users
                         (username, email, password_hash, security_question, security_answer_hash, role)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                         ("Administrator", admin_email, hash_txt(admin_pw),
                          "What is your pet name?", hash_txt("admin"), "Admin"))
        else:
            # keep role correct even if the row already existed with the wrong role
            conn.execute("UPDATE users SET role='Admin' WHERE email=?", (admin_email,))
        conn.commit()


def render_auth_portal():
    init_auth()
    if "token" not in st.session_state:
        st.session_state["token"] = None
    if "auth_tab" not in st.session_state:
        st.session_state["auth_tab"] = "Login"
    if "forgot_method" not in st.session_state:
        st.session_state["forgot_method"] = "Security Question"
    if "forgot_stage" not in st.session_state:
        st.session_state["forgot_stage"] = "choose"
    if "otp_resend_count" not in st.session_state:
        st.session_state["otp_resend_count"] = 0
    if "otp_next_allowed" not in st.session_state:
        st.session_state["otp_next_allowed"] = None

    st.markdown(f"""
    <div style="text-align:center;padding:1.5rem 0 1rem;">
        <div style="font-size:44px;margin-bottom:8px;">⚡</div>
        <h1 style="font-size:2rem !important;margin:0;">FranchiseOps AI Portal</h1>
        <p style="color:{COLORS['text_muted']};font-size:14px;margin:4px 0 0;">Enterprise Multi-Agent Franchise Intelligence System</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        tab1, tab2, tab3 = st.tabs(["🔐 Sign In", "📝 Register Account", "🔑 Reset Password"])

        # ---------------- SIGN IN ---------------- #
        with tab1:
            login_email = st.text_input("Email / Username", key="l_email", placeholder="infosys@ai")
            login_pw = st.text_input("Password", type="password", key="l_pw", placeholder="••••••••")

            if st.button("🚀 Sign In to Portal", key="btn_login"):
                with get_conn() as conn:
                    user = conn.execute(
                        "SELECT id, username, email, password_hash, role, failed_attempts, lock_until, account_status "
                        "FROM users WHERE email=? OR username=?", (login_email, login_email)
                    ).fetchone()

                if not user:
                    st.error("Invalid email/username or password.")
                else:
                    uid, uname, uemail, phash, role, failed, lock_until, status = user
                    now = datetime.datetime.utcnow()

                    if status == 'locked':
                        st.error("❌ Account permanently locked due to 5 failed attempts. Only the System Administrator can unlock this account via the Admin Dashboard.")
                    elif lock_until and datetime.datetime.fromisoformat(lock_until) > now:
                        remaining = int((datetime.datetime.fromisoformat(lock_until) - now).total_seconds())
                        mins = max(1, remaining // 60)
                        st.error(f"⏳ Account temporarily locked. Try again in ~{mins} minute(s).")
                    elif check_txt(login_pw, phash):
                        with get_conn() as conn:
                            conn.execute("UPDATE users SET failed_attempts=0, lock_until=NULL WHERE id=?", (uid,))
                            conn.commit()
                        st.session_state["token"] = make_jwt(uemail, uname)
                        st.session_state["username"] = uname
                        st.session_state["role"] = role
                        st.success(f"Welcome back, {uname} [{role}]!")
                        st.rerun()
                    else:
                        new_failed = (failed or 0) + 1
                        with get_conn() as conn:
                            if new_failed >= 5:
                                conn.execute(
                                    "UPDATE users SET failed_attempts=?, account_status='locked', lock_until=NULL WHERE id=?",
                                    (new_failed, uid))
                                conn.commit()
                                st.error("❌ Account permanently locked due to 5 failed attempts. Only the System Administrator can unlock this account via the Admin Dashboard.")
                            elif new_failed == 4:
                                lock_time = (now + datetime.timedelta(seconds=LOCKOUT_RULES[4])).isoformat()
                                conn.execute("UPDATE users SET failed_attempts=?, lock_until=? WHERE id=?",
                                             (new_failed, lock_time, uid))
                                conn.commit()
                                st.error("⏳ Account temporarily locked for 15 minutes due to 4 failed attempts.")
                            elif new_failed == 3:
                                lock_time = (now + datetime.timedelta(seconds=LOCKOUT_RULES[3])).isoformat()
                                conn.execute("UPDATE users SET failed_attempts=?, lock_until=? WHERE id=?",
                                             (new_failed, lock_time, uid))
                                conn.commit()
                                st.error("⏳ Account temporarily locked for 5 minutes due to 3 failed attempts.")
                            else:
                                conn.execute("UPDATE users SET failed_attempts=? WHERE id=?", (new_failed, uid))
                                conn.commit()
                                st.error("Invalid email/username or password.")

        # ---------------- REGISTER ---------------- #
        with tab2:
            r_user = st.text_input("Username", key="r_u")
            r_email = st.text_input("Email Address", key="r_e")
            r_pw = st.text_input("Create Password", type="password", key="r_p")

            if r_pw:
                level, badge, note = password_strength(r_pw)
                if level == "weak":
                    st.warning(f"{badge} — {note}")
                elif level == "average":
                    st.info(f"{badge} — {note}")
                else:
                    st.success(f"{badge} — {note}")

            r_role = st.selectbox("Select Enterprise Role",
                                   ["Franchise Owner", "Regional Operations Manager", "Store Manager", "Supply Chain Analyst"],
                                   key="r_role")
            r_q = st.selectbox("Security Question",
                                ["What is your pet name?", "What city were you born in?", "What is your favorite school teacher's name?"],
                                key="r_q")
            r_a = st.text_input("Security Answer", key="r_a")

            if st.button("✨ Create Franchisee Account", key="btn_reg"):
                if not (r_user and r_email and r_pw and r_a):
                    st.warning("Please fill out all fields.")
                elif len(r_pw) < 5:
                    st.error("🔴 Password too weak (minimum 5 characters required).")
                else:
                    try:
                        with get_conn() as conn:
                            conn.execute(
                                "INSERT INTO users (username, email, password_hash, security_question, security_answer_hash, role) "
                                "VALUES (?, ?, ?, ?, ?, ?)",
                                (r_user, r_email, hash_txt(r_pw), r_q, hash_txt(r_a.lower().strip()), r_role))
                            conn.commit()
                        st.success(f"Account registered with role [{r_role}]! Please switch to Sign In tab.")
                    except Exception:
                        st.error("Registration failed: Email or username may already exist.")

        # ---------------- FORGOT PASSWORD ---------------- #
        with tab3:
            method = st.radio("Recovery Method", ["Security Question", "OTP via Email"], key="forgot_method_radio")
            st.session_state["forgot_method"] = method

            if method == "Security Question":
                f_email = st.text_input("Registered Email", key="f_e")
                if st.button("Verify Email & Fetch Question", key="btn_f1"):
                    with get_conn() as conn:
                        u = conn.execute("SELECT security_question FROM users WHERE email=?", (f_email,)).fetchone()
                    if u:
                        st.session_state["reset_email"] = f_email
                        st.session_state["reset_q"] = u[0]
                        st.rerun()
                    else:
                        st.error("Email not found.")

                if st.session_state.get("reset_email"):
                    st.info(f"Security Question: **{st.session_state.get('reset_q')}**")
                    ans_try = st.text_input("Enter Answer", key="f_ans")
                    new_pw = st.text_input("New Password", type="password", key="f_npw")
                    if new_pw:
                        level, badge, note = password_strength(new_pw)
                        st.caption(f"{badge} — {note}")

                    if st.button("Confirm Password Reset", key="btn_f2"):
                        with get_conn() as conn:
                            u_hash = conn.execute("SELECT security_answer_hash FROM users WHERE email=?",
                                                   (st.session_state["reset_email"],)).fetchone()
                        if len(new_pw) < 5:
                            st.error("🔴 Password too weak (minimum 5 characters required).")
                        elif u_hash and check_txt(ans_try.lower().strip(), u_hash[0]):
                            with get_conn() as conn:
                                conn.execute("UPDATE users SET password_hash=?, failed_attempts=0, lock_until=NULL, account_status='active' WHERE email=?",
                                             (hash_txt(new_pw), st.session_state["reset_email"]))
                                conn.commit()
                            st.success("Password reset successfully! Please sign in.")
                            st.session_state["reset_email"] = None
                        else:
                            st.error("Incorrect security answer.")

            else:  # OTP via Email
                if st.session_state["forgot_stage"] == "choose":
                    otp_email = st.text_input("Registered Email", key="otp_e")

                    now = datetime.datetime.utcnow()
                    cooldown_active = bool(st.session_state["otp_next_allowed"] and
                        now < st.session_state["otp_next_allowed"])

                    if cooldown_active:
                        remaining = int((st.session_state["otp_next_allowed"] - now).total_seconds())
                        if remaining >= 3600:
                            st.warning("⚠️ Too many OTP requests. Please wait 1 hour before trying again.")
                        elif remaining >= 60:
                            st.warning(f"⏳ Please wait {remaining // 60} minute(s) before requesting another OTP.")
                        else:
                            st.warning(f"⏳ Please wait {remaining} seconds before requesting another OTP.")

                    if st.button("Send OTP", key="btn_send_otp", disabled=cooldown_active):
                        with get_conn() as conn:
                            exists = conn.execute("SELECT id FROM users WHERE email=?", (otp_email,)).fetchone()
                        if not exists:
                            st.error("Email not registered.")
                        else:
                            otp = f"{random.randint(100000, 999999)}"
                            send_otp_email(otp_email, otp)
                            st.session_state["otp_token"] = make_otp_token(otp_email, otp)
                            st.session_state["reset_email_otp"] = otp_email
                            st.session_state["forgot_stage"] = "otp_sent"

                            count = st.session_state["otp_resend_count"] + 1
                            st.session_state["otp_resend_count"] = count
                            cooldowns = {1: 60, 2: 180, 3: 300}
                            wait = cooldowns.get(count, 3600)
                            st.session_state["otp_next_allowed"] = now + datetime.timedelta(seconds=wait)

                            st.success("OTP sent successfully! Check your inbox.")
                            st.rerun()

                elif st.session_state["forgot_stage"] == "otp_sent":
                    st.info(f"Code sent to **{st.session_state['reset_email_otp']}** (valid {OTP_EXPIRY_MINUTES} min).")
                    entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6, key="otp_input")
                    new_pw2 = st.text_input("New Password", type="password", key="otp_npw")
                    if new_pw2:
                        level, badge, note = password_strength(new_pw2)
                        st.caption(f"{badge} — {note}")

                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("Verify & Reset", key="btn_verify_otp"):
                            if len(new_pw2) < 5:
                                st.error("🔴 Password too weak (minimum 5 characters required).")
                            else:
                                ok, msg = verify_otp_token(st.session_state["otp_token"], entered_otp,
                                                            st.session_state["reset_email_otp"])
                                if not ok:
                                    st.error(msg)
                                else:
                                    with get_conn() as conn:
                                        conn.execute(
                                            "UPDATE users SET password_hash=?, failed_attempts=0, lock_until=NULL, account_status='active' WHERE email=?",
                                            (hash_txt(new_pw2), st.session_state["reset_email_otp"]))
                                        conn.commit()
                                    st.session_state["forgot_stage"] = "choose"
                                    st.session_state["otp_resend_count"] = 0
                                    st.session_state["otp_next_allowed"] = None
                                    st.success("Password reset successfully! Please sign in.")
                    with cc2:
                        if st.button("Start Over", key="btn_otp_reset"):
                            st.session_state["forgot_stage"] = "choose"
                            st.rerun()