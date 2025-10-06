# forgot_password_page.py
import streamlit as st

def forgot_password():
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
        st.markdown('<div class="auth-title">Forgot Password</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-desc">No worries! Follow the steps to reset your password.</div>', unsafe_allow_html=True)

        st.info("To reset your password, go to the Reset Password page and enter your email address.")
        if st.button("Go to Reset Password", key="forgot_to_reset"):
            st.session_state["page_choice"] = "Reset Password"
        if st.button("Back to Login", key="forgot_to_login"):
            st.session_state["page_choice"] = "Login"

        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    forgot_password()