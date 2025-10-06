import streamlit as st
from db import SessionLocal
from models import Organization, User, Role, Report, Group
from .utils import safe_rerun

import streamlit as st
from db import SessionLocal
from models import Organization, User, Role, Report, Group
from .utils import safe_rerun

def my_organization_page():
    """Admin view for their organization details and metrics."""
    
    # Add Font Awesome icons (if not already added elsewhere)
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
        <style>
          .card {background: #fff; border-radius: 16px; box-shadow: 0 2px 20px rgba(0,0,0,0.04); padding: 21px 27px 17px 27px; margin-bottom: 14px;}
          .metric-icon {font-size: 2.2em; text-align:center; margin-bottom: 2px;}
          .metric-icon i {font-size: 1.3em; color: #1a1a2b;}
          .user-card {background: #fff; border-radius: 12px; box-shadow: 0 1px 12px rgba(0,0,0,0.03); padding: 16px 20px; margin-bottom: 10px; border-left: 4px solid #3b82f6;}
          .admin-card {border-left: 4px solid #10b981;}
          .report-card {background: #fff; border-radius: 10px; box-shadow: 0 1px 8px rgba(0,0,0,0.03); padding: 14px 18px; margin-bottom: 8px; border-left: 3px solid #8b5cf6;}
          .org-info {background: #f8fafc; border-radius: 12px; padding: 20px; margin-bottom: 20px;}
        </style>
    """, unsafe_allow_html=True)
    
    st.header("My Organization")
    current_user = st.session_state.user
    org_id = current_user.get("organization_id")
    current_admin_role = current_user.get("role_name")

    if not org_id:
        st.error("You are not assigned to an organization yet.")
        return

    s = SessionLocal()
    try:
        org = s.query(Organization).filter_by(id=org_id).first()
        if not org:
            st.error("Organization not found.")
            return

        # Organization info card
        st.markdown(f"""
            <div class="org-info">
                <h3><i class="fa-solid fa-building"></i> {org.name}</h3>
                <p><i class="fa-solid fa-calendar-alt"></i> Created on: {org.created_at.strftime('%B %d, %Y at %H:%M')}</p>
            </div>
        """, unsafe_allow_html=True)

        # Metrics with icons
        total_users = s.query(User).filter_by(organization_id=org_id).count()
        total_admins = s.query(User).filter_by(organization_id=org_id).join(User.role).filter(Role.name=="Admin").count()
        total_reports = s.query(Report).filter_by(organization_id=org_id).count()
        total_groups = s.query(Group).filter_by(organization_id=org_id).count()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-users"></i></div>', unsafe_allow_html=True)
            st.metric("Total Users", total_users)
        with col2:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-user-tie"></i></div>', unsafe_allow_html=True)
            st.metric("Total Admins", total_admins)
        with col3:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-file-lines"></i></div>', unsafe_allow_html=True)
            st.metric("Total Reports", total_reports)
        with col4:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-layer-group"></i></div>', unsafe_allow_html=True)
            st.metric("Total Groups", total_groups)

        # Users section
        st.markdown("### <i class='fa-solid fa-users'></i> Users", unsafe_allow_html=True)
        
        users = s.query(User).filter_by(organization_id=org_id).all()
        current_user_id = current_user.get("id")
        other_users = [u for u in users if u.id != current_user_id]
        current_user_obj = next((u for u in users if u.id == current_user_id), None)

        # Display current user (read-only)
        if current_user_obj:
            st.markdown(f"""
                <div class="user-card admin-card">
                    <div style="display: flex; align-items: center;">
                        <i class="fa-solid fa-user-shield" style="font-size: 1.2em; color: #10b981; margin-right: 10px;"></i>
                        <div>
                            <strong>{current_user_obj.full_name} (You)</strong><br>
                            <small>{current_user_obj.email} • Role: {current_user_obj.role.name if current_user_obj.role else 'User'}</small>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Display other users
        for u in other_users:
            st.markdown(f"""
                <div class="user-card">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center;">
                            <i class="fa-solid fa-user" style="font-size: 1.2em; color: #6b7280; margin-right: 10px;"></i>
                            <div>
                                <strong>{u.full_name}</strong><br>
                                <small>{u.email}</small>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # User management controls
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            
            # Prepare role options
            role_options = [r.name for r in s.query(Role).all()]
            if current_admin_role != "Superadmin":
                role_options = [r for r in role_options if r != "Superadmin"]
            if u.organization_id is not None and "Superadmin" in role_options:
                role_options.remove("Superadmin")

            with col2:
                role_name = u.role.name if u.role else "User"
                st.selectbox(
                    "Role",
                    options=role_options,
                    index=role_options.index(role_name) if role_name in role_options else 0,
                    key=f"role_{u.id}",
                    on_change=update_user_role,
                    args=(u.id,)
                )
            with col3:
                if st.button("✏️ Edit", key=f"edit_{u.id}"):
                    edit_user(u.id)
            with col4:
                if st.button("🗑️ Delete", key=f"delete_{u.id}"):
                    delete_user(u.id)
                    safe_rerun()

        # Recent reports section
        st.markdown("### <i class='fa-solid fa-file-lines'></i> Recent Reports", unsafe_allow_html=True)
        reports = s.query(Report).filter_by(organization_id=org_id).order_by(Report.created_at.desc()).limit(10).all()
        
        if reports:
            for r in reports:
                owner = s.query(User).filter_by(id=r.owner_id).first()
                owner_name = owner.full_name if owner else "Unknown"
                st.markdown(f"""
                    <div class="report-card">
                        <div style="display: flex; align-items: center;">
                            <i class="fa-solid fa-file-alt" style="color: #8b5cf6; margin-right: 10px;"></i>
                            <div>
                                <strong>{r.title}</strong><br>
                                <small>Uploaded by: {owner_name} • {r.created_at.strftime('%B %d, %Y at %H:%M')}</small>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No reports uploaded yet.")

    finally:
        s.close()







def update_user_role(user_id):
    """Update user role when changed from selectbox"""
    s = SessionLocal()
    try:
        new_role_name = st.session_state[f"role_{user_id}"]
        user = s.query(User).filter_by(id=user_id).first()
        current_admin_role = st.session_state.user.get("role_name")

        # Restrict Superadmin assignment
        if new_role_name == "Superadmin":
            if current_admin_role != "Superadmin":
                st.warning("Only Superadmin can assign this role.")
                return
            if user.organization_id is not None:
                st.warning("Only users not in any organization can be made Superadmin.")
                return

        role = s.query(Role).filter_by(name=new_role_name).first()
        if user and role:
            user.role_id = role.id
            s.commit()
            st.success(f"Role updated to {new_role_name}")
    finally:
        s.close()


def edit_user(user_id):
    """Edit user information"""
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            st.error("User not found")
            return

        with st.form(f"edit_user_form_{user_id}"):
            full_name = st.text_input("Full Name", value=user.full_name)
            email = st.text_input("Email", value=user.email)
            submitted = st.form_submit_button("Save Changes")
            if submitted:
                user.full_name = full_name
                user.email = email
                s.commit()
                st.success("User information updated!")
                safe_rerun()
    finally:
        s.close()


def delete_user(user_id):
    """Delete a user"""
    s = SessionLocal()
    try:
        user = s.query(User).filter_by(id=user_id).first()
        if not user:
            st.error("User not found.")
            return
        s.delete(user)
        s.commit()
        st.success("User deleted successfully! 🗑️")
    finally:
        s.close()
