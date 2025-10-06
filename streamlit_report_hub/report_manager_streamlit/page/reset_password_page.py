
import streamlit as st
from db import SessionLocal
from models import User
from modules.auth import hash_password
from modules.utils import safe_rerun

def reset_password():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <style>
                .auth-container {background: #fff; border-radius: 18px; box-shadow: 0 2px 16px rgba(0,0,0,0.04); padding: 38px 40px 28px 40px; margin-top: 48px;}
                .auth-title { font-size: 2.2rem; font-weight: bold; text-align:center; margin-bottom: .25rem;}
                .auth-desc {color:#888; text-align:center; margin-bottom:1.8rem;}
                .auth-logo {display:flex; justify-content:center; margin-bottom:1rem;}
                .small-link {text-align:center; margin-top:1.5rem; margin-bottom:0;}
            </style>
        """, unsafe_allow_html=True)
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<div class="auth-logo"><img src="https://img.icons8.com/ios-filled/48/15131c/report-card.png"/></div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Reset Password</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-desc">Create a brand new password for your account.</div>', unsafe_allow_html=True)

        email = st.text_input("Email", placeholder="Enter your email", key="reset_email")
        if not email:
            st.warning("Please provide an email address.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        session = SessionLocal()
        try:
            user = session.query(User).filter_by(email=email).first()
            if not user:
                st.error("Email not found.")
                st.markdown('</div>', unsafe_allow_html=True)
                return

            with st.form("reset_password_form"):
                new_password = st.text_input("New Password", type="password", placeholder="New password")
                confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                submitted = st.form_submit_button("Save New Password")
                if submitted:
                    if not new_password or not confirm_password:
                        st.error("Please enter and confirm your new password.")
                        return
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                        return
                    user.password_hash = hash_password(new_password)
                    session.commit()
                    st.success("Password updated successfully. Redirecting to login page...")
                    safe_rerun()
        finally:
            session.close()
        st.markdown("""
        <style>
        div.stButton > button:first-child {
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
    if st.button("Forgot your password?"):
        st.session_state["page_choice"] = "Forgot Password"

        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    reset_password()
