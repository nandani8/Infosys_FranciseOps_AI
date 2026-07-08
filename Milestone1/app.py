
import streamlit as st
import json
import os
import re
import jwt
import datetime
import smtplib
import random
from email.message import EmailMessage

JWT_SECRET = "my_super_secret_key_12345"

# Replace these with your Gmail and App Password while developing
EMAIL_ADDRESS = "sahanandani061@gmail.com"
EMAIL_PASSWORD = "dhen ntvy ceoh puqp"

def send_otp(receiver_email):

    otp = str(random.randint(100000, 999999))

    msg = EmailMessage()
    msg["Subject"] = "Your OTP for Password Reset"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email

    msg.set_content(f"Your OTP is: {otp}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

    return otp


st.set_page_config(
    page_title="User Authentication System",
    page_icon="🔐",
    layout="centered"
)

st.title("🔐 User Authentication System")
# ---------------- DASHBOARD ---------------- #

if "token" in st.session_state:

    st.title("🏠 User Dashboard")

    st.success(f"Welcome, {st.session_state['username']}!")

    if st.button("Logout"):

        del st.session_state["token"]
        del st.session_state["username"]

        st.rerun()

    st.stop()

menu = st.sidebar.radio(
    "Navigation",
    ["Login", "Signup", "Forgot Password", "Admin Login"]
)

# ---------------- LOGIN ---------------- #
# ---------------- LOGIN ---------------- #
if menu == "Login":

    st.header("User Login")

    username = st.text_input("Username / Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if os.path.exists("users.json"):
            with open("users.json", "r") as f:
                users = json.load(f)
        else:
            users = []

        found = False

        for user in users:

            if (
                (user["username"] == username or user["email"] == username)
                and user["password"] == password
            ):

                found = True

                payload = {
                    "username": user["username"],
                    "email": user["email"],
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                }

                token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

                st.session_state["token"] = token
                st.session_state["username"] = user["username"]

                st.success("Login Successful!")

        if not found:
            st.error("Invalid Username or Password")

# ---------------- SIGNUP ---------------- #

# ---------------- SIGNUP ---------------- #

elif menu == "Signup":

    st.header("Create Account")

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

    if st.button("Create Account"):

        # 1. Mandatory fields
        if not all([username, email, password, confirm_password, answer]):
            st.error("Please fill all fields.")

        # 2. Confirm Password
        elif password != confirm_password:
            st.error("Passwords do not match.")

        # 3. Email Validation
        elif not re.match(r'^[A-Za-z0-9._%+-]{2,}@[A-Za-z]{2,}\.[A-Za-z]{2,}$', email):
            st.error("Enter a valid email address.")

        # 4. Password Validation
        elif not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$', password):
            st.error(
                "Password must be at least 8 characters and contain uppercase, lowercase, number and special symbol."
            )

        else:

            # Load existing users
            if os.path.exists("users.json"):
                with open("users.json", "r") as f:
                    users = json.load(f)
            else:
                users = []

            # Check duplicate username
            for user in users:
                if user["username"] == username:
                    st.error("Username already exists.")
                    st.stop()

            # Save new user
            users.append({
                "username": username,
                "email": email,
                "password": password,
                "security_question": question,
                "security_answer": answer
            })

            with open("users.json", "w") as f:
                json.dump(users, f, indent=4)

            st.success("Account created successfully!")


# ---------------- FORGOT PASSWORD ---------------- #

elif menu == "Forgot Password":

    st.header("Forgot Password")

    option = st.radio(
        "Choose Recovery Method",
        [
            "Security Question",
            "OTP via Email"
        ]
    )

    # ---------- Security Question Recovery ---------- #

    if option == "Security Question":

        username = st.text_input("Username")

        if username:

            if os.path.exists("users.json"):
                with open("users.json", "r") as f:
                    users = json.load(f)
            else:
                users = []

            current_user = None

            for user in users:
                if user["username"] == username:
                    current_user = user
                    break

            if current_user:

                st.write("### Security Question")
                st.info(current_user["security_question"])

                answer = st.text_input("Security Answer")

                new_password = st.text_input("New Password", type="password")

                confirm_password = st.text_input("Confirm Password", type="password")

                if st.button("Reset Password"):

                    if answer != current_user["security_answer"]:
                        st.error("Incorrect security answer.")

                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")

                    elif not re.match(
                        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$',
                        new_password
                    ):
                        st.error(
                            "Password must contain uppercase, lowercase, number and special symbol."
                        )

                    else:

                        current_user["password"] = new_password

                        with open("users.json", "w") as f:
                            json.dump(users, f, indent=4)

                        st.success("Password updated successfully!")

            else:
                st.error("Username not found.")

    # ---------- OTP Recovery ---------- #

    else:

        email = st.text_input("Registered Email")

        if st.button("Send OTP"):

            if os.path.exists("users.json"):
                with open("users.json", "r") as f:
                    users = json.load(f)
            else:
                users = []

            registered = False

            for user in users:

                if user["email"] == email:

                    registered = True

                    otp = send_otp(email)

                    st.session_state["otp"] = otp
                    st.session_state["reset_email"] = email

                    st.success("OTP sent successfully!")

                    break

            if not registered:
                st.error("Email not registered.")

        entered_otp = st.text_input("Enter OTP")

        new_password = st.text_input("New Password", type="password")

        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Verify OTP"):

            if "otp" not in st.session_state:
                st.error("Please generate an OTP first.")

            elif entered_otp != st.session_state["otp"]:
                st.error("Invalid OTP.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            elif not re.match(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$',
                new_password
            ):
                st.error(
                    "Password must contain uppercase, lowercase, number and special symbol."
                )

            else:

                with open("users.json", "r") as f:
                    users = json.load(f)

                for user in users:

                    if user["email"] == st.session_state["reset_email"]:

                        user["password"] = new_password
                        break

                with open("users.json", "w") as f:
                    json.dump(users, f, indent=4)

                del st.session_state["otp"]
                del st.session_state["reset_email"]

                st.success("Password updated successfully!")

# ---------------- ADMIN ---------------- #

elif menu == "Admin Login":

    st.header("Admin Login")

    admin = st.text_input("Admin Username")

    password = st.text_input("Admin Password", type="password")

    if st.button("Admin Login"):
        st.info("Admin Dashboard will be added later.")
