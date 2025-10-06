import streamlit as st
from db import SessionLocal
from models import User, Role
from modules.auth import hash_password, superadmin_exists
from modules.utils import safe_rerun

def register_via_token():
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
        st.markdown('<div class="auth-title">Complete Registration</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-desc">Finish setting up your account</div>', unsafe_allow_html=True)

        if "show_register_form" not in st.session_state:
            st.session_state.show_register_form = True

        if st.session_state.show_register_form:
            with st.form("form_register_token"):
                token = st.text_input("Invite token", placeholder="Paste your invite token", key="reg_token")
                name = st.text_input("Full name", placeholder="Enter your name", key="reg_name")
                password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_password")
                submitted = st.form_submit_button("Complete registration")
                if submitted:
                    if not token or not name or not password:
                        st.error("Provide token, full name, and password.")
                        return
                    s = SessionLocal()
                    try:
                        user = s.query(User).filter_by(invite_token=token).first()
                        if not user:
                            st.error("Invalid or expired token.")
                            return
                        user.full_name = name
                        user.password_hash = hash_password(password)
                        user.invite_token = None
                        s.commit()
                        st.success("Registration complete, please login.")
                        st.session_state.show_register_form = False
                    finally:
                        s.close()
        if st.button("Back to Login", key="register_to_login"):
            st.session_state["page_choice"] = "Login"

        st.markdown('</div>', unsafe_allow_html=True)
        
        
        
        
        
def create_superadmin_flow():
    """Create the first Superadmin (top-level role, organization_id = None)"""
    if superadmin_exists():
        return

    st.info("Create the first Superadmin (top-level role, not tied to any organization).")
    with st.form("form_create_superadmin"):
        full_name = st.text_input("Full name", key="sa_name")
        email = st.text_input("Email", key="sa_email")
        password = st.text_input("Password", type="password", key="sa_password")
        submitted = st.form_submit_button("Create Superadmin")
        
        if submitted:
            if not full_name or not email or not password:
                st.error("Please provide name, email, and password.")
                return
            
            s = SessionLocal()
            try:
                super_role = s.query(Role).filter_by(name="Superadmin").first()
                if not super_role:
                    st.error("Superadmin role not found. Run init_db again.")
                    return
                if s.query(User).filter_by(email=email).first():
                    st.error("A user with that email already exists.")
                    return

                user = User(
                    full_name=full_name,
                    email=email,
                    password_hash=hash_password(password),
                    role_id=super_role.id,
                    organization_id=None
                )
                s.add(user)
                s.commit()
                st.success("Superadmin created. Please log in.")

                # Clear form by rerunning (no direct session state modification)
                safe_rerun()

            except Exception as e:
                s.rollback()
                st.error(f"Error creating Superadmin: {e}")
            finally:
                s.close()