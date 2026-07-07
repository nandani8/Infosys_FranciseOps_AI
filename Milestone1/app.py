import streamlit as st

st.set_page_config(
    page_title="User Authentication",
    page_icon="🔐",
    layout="centered"
)

st.title("🔐 User Authentication Module")

page = st.sidebar.selectbox(
    "Choose a Page",
    ["Login", "Signup", "Forgot Password", "Admin Login"]
)

if page == "Login":
    st.header("Login")
    username = st.text_input("Username / Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        st.success("Login button clicked!")

elif page == "Signup":
    st.header("Signup")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    question = st.selectbox(
        "Security Question",
        [
            "What is your pet's name?",
            "What is your favourite color?",
            "What is your birthplace?"
        ]
    )

    answer = st.text_input("Security Answer")

    if st.button("Create Account"):
        st.success("Signup button clicked!")

elif page == "Forgot Password":
    st.header("Forgot Password")
    st.info("Forgot Password page will be added next.")

else:
    st.header("Admin Login")
    admin_user = st.text_input("Admin Username")
    admin_pass = st.text_input("Admin Password", type="password")

    if st.button("Admin Login"):
        st.success("Admin Login button clicked!")
