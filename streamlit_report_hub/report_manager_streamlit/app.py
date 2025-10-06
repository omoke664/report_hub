# app.py
import streamlit as st
from db import init_db
from models import User, Organization, Role, Group, Base
from modules.auth import logout, invite_user_flow, users_and_invites_view, superadmin_org_management
from modules.groups import group_management_page
from modules.reports import reports_page
from modules.utils import safe_rerun
from page.login_page import login
from page.register_page import register_via_token
from page.forgot_password_page import forgot_password
from page.reset_password_page import reset_password
from modules.organization import my_organization_page
from page.dashboard_page import dashboards_main_page 
from page.home_page import home_page 


import os
# Initialize DB and upload directory
init_db(Base, Role)
UPLOAD_DIR = 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Report Manager (Streamlit)", layout="wide")

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
""", unsafe_allow_html=True)


def main_app():
    # --- Session state initialization ---
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.user = {}
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "role" not in st.session_state:
        st.session_state.role = None

    # --- Login / Registration / Forgot Password / Reset Password ---
    if not st.session_state.authenticated:
        st.title("Welcome to the Report Management System")
        query_params = st.query_params
        if "token" in query_params:
            token = query_params["token"][0]
            reset_password()
        else:
    # --- unified navigation key ---
            if "page_choice" not in st.session_state:
                st.session_state["page_choice"] = "Login"

            # Only show the radio selector if we're on a main screen (e.g. login)
            if st.session_state["page_choice"] in ["Login", "Register (via invite token)", "Forgot Password", "Reset Password"]:
                widget_choice = st.radio(
                    "Select an option:",
                    ["Login", "Register (via invite token)", "Forgot Password", "Reset Password"],
                    key="auth_choice_widget",
                    index=["Login", "Register (via invite token)", "Forgot Password", "Reset Password"].index(st.session_state["page_choice"])
                )
                if widget_choice != st.session_state["page_choice"]:
                    st.session_state["page_choice"] = widget_choice
                    safe_rerun()

            page_choice = st.session_state["page_choice"]

            # --- route based on session_state ---
            if page_choice == "Login":
                login()
            elif page_choice == "Register (via invite token)":
                register_via_token()
            elif page_choice == "Forgot Password":
                forgot_password()
            elif page_choice == "Reset Password":
                reset_password()
    # Allow manual entry if token is lost
            return

    # --- Sidebar ---
    role = st.session_state.user.get("role_name", "Guest")
    st.sidebar.title("Navigation")
    if st.sidebar.button("Logout"):
        logout()
        return

    st.write(f"Logged in as: {st.session_state.user.get('email', 'Not logged in')} ({role})")

    # Sidebar menu based on role
    if role == "Superadmin":
        menu = st.sidebar.radio(
            "Go to", 
            ["Home", "Manage Organizations", "Users & Invites"]
        )
    elif role == "Admin":
        menu = st.sidebar.radio(
            "Go to", 
            ["Home", "My Organization", "Groups", "Invite Users", "My Reports", "Dashboards"]
        )
    else:  # regular User
        menu = st.sidebar.radio(
            "Go to", 
            ["Home", "My Reports", "Dashboards"]
        )

    # --- Menu routing ---
    if menu == "Home":
        if menu == "Home":
            home_page()
    elif menu == "Manage Organizations":
        superadmin_org_management()
    elif menu == "Users & Invites":
        users_and_invites_view()
    elif menu == "Invite Users":
        invite_user_flow()
    elif menu == "My Organization":
        
        my_organization_page()
    elif menu == "Groups":
        group_management_page()
    elif menu == "Dashboards":
        dashboards_main_page()
    elif menu == "My Reports":
        # Only Admins/Users see this
        user = st.session_state.user
        default_choice = 'View Reports' if st.session_state.get('upload_success') else 'Upload Report'
        can_upload = True if user['role_name'] in ['Admin', 'User'] else False

        choice = st.radio(
            'Choose action',
            ['Upload Report', 'View Reports'],
            index=0 if default_choice == 'Upload Report' else 1
        )
        if choice == 'Upload Report' and can_upload:
            # Set session state to show upload form within reports_page
            st.session_state.show_upload = True
            reports_page()
            if st.session_state.get('upload_success'):
                st.session_state.upload_success = False
                st.session_state.show_upload = False  # Reset after success
                safe_rerun()
        else:
            # Set session state to hide upload and show reports (default behavior)
            st.session_state.show_upload = False
            st.session_state.current_folder = None  # Reset folder to show all owned reports
            reports_page()

if __name__ == "__main__":
    main_app()