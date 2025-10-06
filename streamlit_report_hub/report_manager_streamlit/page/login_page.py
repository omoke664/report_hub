import streamlit as st
from db import SessionLocal
from models import User
from modules.auth import verify_password
from modules.utils import safe_rerun

def login():
    col1, col2, col3 = st.columns([1, 2, 1])  # centers the form

    with col2:
        # Custom CSS for styling
        st.markdown("""
            <style>
                .auth-container {
                    background: #fff;
                    border-radius: 18px;
                    box-shadow: 0 2px 16px rgba(0,0,0,0.04);
                    padding: 38px 40px 28px 40px;
                    margin-top: 48px;
                }
                .auth-title { font-size: 2.2rem; font-weight: bold; text-align:center; margin-bottom: .25rem;}
                .auth-desc {color:#888; text-align:center; margin-bottom:1.8rem;}
                .auth-logo {display:flex; justify-content:center; margin-bottom:1rem;}
                .small-link {text-align:center; margin-top:1.5rem; margin-bottom:0;}
            </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-logo"><img src="https://img.icons8.com/ios-filled/48/15131c/report-card.png"/></div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">ReportHub</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-desc">Sign in to your account</div>', unsafe_allow_html=True)
        st.subheader("Welcome back")
        st.caption("Enter your credentials to access your dashboard")

        session = SessionLocal()
        email = st.text_input("Email", placeholder="Enter your email", key="login_email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        login_button = st.button("Sign in")

        if login_button:
            user = session.query(User).filter_by(email=email).first()
            if user and verify_password(password, user.password_hash):
                st.session_state.user = {
                    "id": user.id,
                    "email": user.email,
                    "role_name": user.role.name if user.role else "User",
                    "organization_id": user.organization_id
                }
                st.session_state.authenticated = True
                st.session_state.role = st.session_state.user["role_name"]
                st.success(f"Logged in as {st.session_state.user['email']} ({st.session_state.role})")
                session.close()
                safe_rerun()
            else:
                st.error("Invalid email or password")
                session.close()

        st.markdown("""
        <style>
        div.stButton > button.link-button {
            background: none!important;
            color: #15131c!important;
            border: none;
            padding: 0;
            font-size: 1em;
            text-decoration: underline;
            cursor: pointer;
        }
        </style>
    """, unsafe_allow_html=True)
    if st.button("Forgot your password?", key="to_forgot", help="Reset password", kwargs={"className": "link-button"}):
        st.session_state["page_choice"] = "Forgot Password"

        st.markdown('</div>', unsafe_allow_html=True)
