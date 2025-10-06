
from passlib.hash import pbkdf2_sha256
import secrets
from db import SessionLocal, get_session
from models import User, Organization, Role
import streamlit as st
from .utils import safe_rerun
import os
import logging


st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
      .org-card {background: #fff; border-radius: 15px; box-shadow: 0 2px 18px rgba(0,0,0,0.06); padding: 20px 26px 18px 26px; margin-bottom: 14px;}
      .org-card h4 {margin:0;}
      .org-card .meta {color: #868fa1; font-size: .96em;}
      .org-card .org-actions {margin-top: 12px;}
      .org-card .org-actions button {margin-right: 12px;}
      .org-new {background: #f6fafe;border-radius:10px;padding:20px;margin-bottom:18px;}
    </style>
""", unsafe_allow_html=True)


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-SHA256."""
    return pbkdf2_sha256.hash(password)

def verify_password(password: str, hash_: str) -> bool:
    """Verify a password against its hash."""
    return pbkdf2_sha256.verify(password, hash_)

def create_invite(inviter_id: str, email: str, org_id: str, role_name: str) -> str:
    """
    Create an invite token for a user to join an organization with the specified role.
    """
    token = secrets.token_urlsafe(16)
    session = get_session()
    if not session:
        raise Exception("Failed to create database session")
    
    try:
        inviter = session.query(User).filter_by(id=inviter_id).first()
        if not inviter:
            raise ValueError("Invalid inviter")

        inviter_role = session.query(Role).filter_by(id=inviter.role_id).first()
        if not inviter_role:
            raise ValueError("Inviter has no role")

        # Validate role selection
        if role_name not in ["User", "Admin"]:
            raise ValueError("Invalid role selected")
        if role_name == "Admin" and inviter_role.name != "Superadmin":
            raise PermissionError("Only Superadmins can invite users as Admins")

        if inviter_role.name == "Admin" and inviter.organization_id != org_id:
            raise PermissionError("Admin can only invite users into their own organization")
        elif inviter_role.name not in ["Admin", "Superadmin"]:
            raise PermissionError("Only Admins or Superadmins can create invites")

        # Get the role for the invitee
        invitee_role = session.query(Role).filter_by(name=role_name).first()
        if not invitee_role:
            raise ValueError(f"Role '{role_name}' not found in database")

        user = session.query(User).filter_by(email=email).first()
        if user:
            user.invite_token = token
            user.organization_id = org_id
            user.role_id = invitee_role.id  # Update role for existing user
        else:
            user = User(
                full_name="",
                email=email,
                password_hash="",
                invite_token=token,
                organization_id=org_id,
                role_id=invitee_role.id
            )
            session.add(user)

        session.commit()
        logger.debug(f"Invite token generated for {email}: {token}, role: {role_name}")
        return token

    except Exception as e:
        session.rollback()
        logger.error(f"Error in create_invite for {email}: {e}")
        raise e
    finally:
        session.close()

def superadmin_exists():
    """Return True if a Superadmin user exists."""
    s = get_session()
    if not s:
        return False
    try:
        super_role = s.query(Role).filter_by(name="Superadmin").first()
        if not super_role:
            return False
        count = s.query(User).filter_by(role_id=super_role.id).count()
        return count > 0
    finally:
        s.close()

def get_role_name(role_id):
    """Return the role name for a role_id (or None)."""
    s = get_session()
    if not s:
        return None
    try:
        role = s.query(Role).filter_by(id=role_id).first()
        return role.name if role else None
    finally:
        s.close()

def logout():
    st.session_state.user = {}
    st.session_state.authenticated = False
    st.session_state.role = None
    st.success("You have been logged out")
    safe_rerun()

def invite_user_flow():
    """Admin page: invite a user into the admin's organization."""
    st.header("Invite a user to your organization")
    org_id = st.session_state.user.get("organization_id")
    if not org_id:
        st.error("Your account is not tied to an organization (cannot invite).")
        return
    
    # Restrict role options based on inviter's role
    role_options = ["User"]
    if st.session_state.user.get("role_name") == "Superadmin":
        role_options.append("Admin")
    
    with st.form("form_invite_user"):
        email = st.text_input("Invitee email", key="invitee_email")
        role_select = st.selectbox("Role for invitee", role_options, index=0)
        submitted = st.form_submit_button("Invite")
        if submitted:
            if not email:
                st.error("Provide an invitee email.")
                return
            try:
                # Pass the selected role to create_invite
                token = create_invite(st.session_state.user["id"], email, org_id, role_select)
                st.success(f"Invite created for {email} as {role_select}. Token: {token}")
                st.info("Copy this token and send it to the invited user (or set up email sending).")
            except Exception as e:
                st.error(str(e))

def users_and_invites_view():
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
        <style>
            .org-card {background:#fff; border-radius:13px; box-shadow:0 1px 10px #eaeaea; padding:16px 20px; margin-bottom:15px;}
            .user-listing, .invite-listing {margin-left: 12px; margin-bottom:5px;}
            .avatar {display:inline-block;width:34px;height:34px;background:#e6edfa;border-radius:99px;color:#2d5491;text-align:center;line-height:34px;font-weight:bold;font-size:1.09em;margin-right:12px;}
            .user-badge {display:inline-block; background:#f1f5f9;color:#274060;border-radius:6px;
                font-size:0.94em; padding: 2px 12px; margin-right:10px;}
            .user-row {display:flex;align-items:center;gap:12px;font-size:1.08em;margin-bottom:2px;}
            .user-role {background:#eff6ff; color:#305a89; border-radius:6px; padding:1px 9px; font-size:.94em;}
            .invite-row {margin-bottom:3px;}
            .invite-token {background:#fcf4e3;color:#a86521;border-radius:6px;padding:0px 7px;}
            .actions {display:inline-block;}
            .actions button {margin-right:6px;}
        </style>
    """, unsafe_allow_html=True)
    s = get_session()
    if not s:
        st.error("Failed to connect to database.")
        return
    try:
        role = st.session_state["user"]["role_name"]
        if role == "Superadmin":
            st.header("All Organizations and Users")
            orgs = s.query(Organization).all()
            for org in orgs:
                with st.expander(f"{org.name} (ID: {org.id})", expanded=False):
                    users = s.query(User).filter_by(organization_id=org.id).all()
                    if users:
                        st.markdown("<div style='margin-bottom:4px;font-weight:500;color:#37588a;'>Users:</div>", unsafe_allow_html=True)
                        for u in users:
                            role_name = get_role_name(u.role_id) or "Unknown"
                            user_icon = "fa-user-tie" if role_name == "Admin" else "fa-user"
                            avatar_letters = "".join(part[0].upper() for part in (u.full_name or "?").split()[:2])
                            st.markdown(
                                f"<div class='user-listing user-row'>"
                                f"<span class='avatar'><i class='fa-solid {user_icon}'></i></span>"
                                f"<span class='user-badge'>{u.full_name or '(no name)'}</span> "
                                f"{u.email} "
                                f"<span class='user-role'><i class='fa-solid fa-tag'></i> {role_name}</span>"
                                f"{' <i class=\"fa-regular fa-paper-plane\"></i> <b>Invite Pending</b>' if u.invite_token else ''}"
                                f"</div>", unsafe_allow_html=True)
                    else:
                        st.write("No users in this org.")

                    invites = s.query(User).filter_by(organization_id=org.id).filter(User.invite_token != None).all()
                    if invites:
                        st.markdown("<div style='margin:.7em 0 .2em 1px;font-weight:500;color:#3d3636;'>"
                            "<i class='fa-regular fa-paper-plane'></i> Pending Invites:</div>", unsafe_allow_html=True)
                        for inv in invites:
                            role_name = get_role_name(inv.role_id) or "Unknown"
                            st.markdown(
                                f"<div class='invite-listing invite-row'>"
                                f"<span class='avatar'><i class='fa-solid fa-user-plus'></i></span>"
                                f"{inv.email} <span class='user-role'>{role_name}</span> "
                                f"<span class='invite-token'>{inv.invite_token}</span>"
                                f"<span class='actions'>"
                                f"{st.button('Resend', key=f'resend_{inv.id}') and ' - <b>Invite resent!</b>' or ''}"
                                f"{st.button('Cancel', key=f'cancel_{inv.id}') and ' - <span style=\"color:#d92d20;\"><b>Invite canceled!</b></span>' or ''}"
                                f"</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:#bcbcbc;'>No pending invites.</span>", unsafe_allow_html=True)
        elif role == "Admin":
            st.header("Users and Pending Invites for Your Organization")
            org_id = st.session_state.user["organization_id"]
            if not org_id:
                st.error("No organization associated with your account.")
                return
            st.markdown("<div class='org-card'>", unsafe_allow_html=True)
            users = s.query(User).filter_by(organization_id=org_id).all()
            if users:
                st.markdown("<div style='margin-bottom:4px;font-weight:500;color:#37588a;'>Users:</div>", unsafe_allow_html=True)
                for u in users:
                    role_name = get_role_name(u.role_id) or "Unknown"
                    user_icon = "fa-user-tie" if role_name == "Admin" else "fa-user"
                    avatar_letters = "".join(part[0].upper() for part in (u.full_name or "?").split()[:2])
                    st.markdown(
                        f"<div class='user-listing user-row'>"
                        f"<span class='avatar'><i class='fa-solid {user_icon}'></i></span>"
                        f"<span class='user-badge'>{u.full_name or '(no name)'}</span> "
                        f"{u.email} "
                        f"<span class='user-role'><i class='fa-solid fa-tag'></i> {role_name}</span>"
                        f"{' <i class=\"fa-regular fa-paper-plane\"></i> <b>Invite Pending</b>' if u.invite_token else ''}"
                        f"</div>", unsafe_allow_html=True)
            else:
                st.write("No users in your org yet.")

            st.markdown("<div style='margin:.99em 0 .2em 1px;font-weight:500;color:#3d3636;'>"
                        "<i class='fa-regular fa-paper-plane'></i> Pending Invites:</div>", unsafe_allow_html=True)
            invites = s.query(User).filter_by(organization_id=org_id).filter(User.invite_token != None).all()
            if invites:
                for inv in invites:
                    role_name = get_role_name(inv.role_id) or "Unknown"
                    st.markdown(
                        f"<div class='invite-listing invite-row'>"
                        f"<span class='avatar'><i class='fa-solid fa-user-plus'></i></span>"
                        f"{inv.email} <span class='user-role'>{role_name}</span>"
                        f"<span class='invite-token'>{inv.invite_token}</span>"
                        f"<span class='actions'>"
                        f"{st.button('Resend', key=f'resend_{inv.id}') and ' - <b>Invite resent!</b>' or ''}"
                        f"{st.button('Cancel', key=f'cancel_{inv.id}') and ' - <span style=\"color:#d92d20;\"><b>Invite canceled!</b></span>' or ''}"
                        f"</span></div>", unsafe_allow_html=True)
            else:
                st.write("No pending invites.")
            st.markdown("</div>", unsafe_allow_html=True)
    finally:
        s.close()


def superadmin_org_management():
    """Superadmin page to create, edit, and delete organizations."""
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
        <style>
          .org-card {background: #fff; border-radius: 15px; box-shadow: 0 2px 18px rgba(0,0,0,0.06); padding: 20px 26px 18px 26px; margin-bottom: 14px;}
          .org-card h4 {margin:0;}
          .org-card .meta {color: #868fa1; font-size: .96em;}
          .org-card .org-actions {margin-top: 12px;}
          .org-card .org-actions button {margin-right: 12px;}
          .org-new {background: #f6fafe;border-radius:10px;padding:20px;margin-bottom:18px;}
        </style>
    """, unsafe_allow_html=True)

    s = get_session()
    if not s:
        st.error("Failed to connect to database.")
        return
    try:
        st.header("Manage Organizations")
        st.subheader("Create New Organization")
        with st.expander("➕ Add New Organization", expanded=True):
            # Always use session state for instant visibility toggle
            org_name = st.text_input("Organization name", key="org_name")
            create_admin_now = st.checkbox("Create an admin now?", key="create_admin_now")
            admin_name = admin_email = ""
            if st.session_state.get("create_admin_now"):
                st.markdown("""
                    <div style="background:#f9fbfd; border-radius:9px; padding:16px 18px; margin-top:8px; margin-bottom:12px;">
                        <i class="fa-solid fa-user-tie"></i> <b>New Admin Details</b>
                    </div>
                """, unsafe_allow_html=True)
                admin_name = st.text_input("Admin full name", key="new_admin_name")
                admin_email = st.text_input("Admin email", key="new_admin_email")
            submitted = st.button("Create Organization")
            if submitted:
                org_name = st.session_state.get("org_name")
                create_admin_now = st.session_state.get("create_admin_now")
                admin_name = st.session_state.get("new_admin_name", "")
                admin_email = st.session_state.get("new_admin_email", "")
                if not org_name:
                    st.error("Organization name required.")
                elif s.query(Organization).filter_by(name=org_name).first():
                    st.error("Organization with this name already exists.")
                else:
                    try:
                        org = Organization(name=org_name)
                        s.add(org)
                        s.flush()
                        invite_token = None
                        if create_admin_now:
                            if not admin_name or not admin_email:
                                st.error("Provide admin name and email.")
                                s.rollback()
                                return
                            if s.query(User).filter_by(email=admin_email).first():
                                st.error("User with that email already exists.")
                                s.rollback()
                                return
                            import secrets
                            invite_token = secrets.token_urlsafe(16)
                            admin_role = s.query(Role).filter_by(name="Admin").first()
                            admin_user = User(
                                full_name=admin_name,
                                email=admin_email,
                                password_hash="",
                                role_id=admin_role.id,
                                organization_id=org.id,
                                invite_token=invite_token,
                            )
                            s.add(admin_user)
                        s.commit()
                        if create_admin_now and invite_token:
                            st.success(f"<i class='fa-solid fa-building'></i> Organization '<b>{org_name}</b>' created and admin '<b>{admin_name}</b>' invited.<br>Invite token: <code>{invite_token}</code>", unsafe_allow_html=True)
                        else:
                            st.success(f"<i class='fa-solid fa-building'></i> Organization '<b>{org_name}'</b> created successfully.", unsafe_allow_html=True)
                        safe_rerun()
                    except Exception as e:
                        s.rollback()
                        st.error(f"Error creating organization: {e}")

        st.subheader("Existing Organizations")
        organizations = s.query(Organization).all()
        if not organizations:
            st.info("No organizations exist yet.")
        else:
            for org in organizations:
                num_users = s.query(User).filter_by(organization_id=org.id).count()
                st.markdown(f"""
                  <div class="org-card">
                    <h4><i class="fa-solid fa-building" style="color:#4566cb"></i> {org.name}</h4>
                    <div class="meta">
                      <i class="fa-solid fa-users"></i> {num_users} users
                      &nbsp; • &nbsp; <i class="fa-regular fa-calendar"></i> Created: {org.created_at.strftime('%Y-%m-%d %H:%M')}
                    </div>
                    <div class="org-actions">
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{org.id}"):
                        st.session_state.edit_org_id = org.id
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{org.id}"):
                        st.session_state.delete_org_id = org.id
                st.markdown("</div>", unsafe_allow_html=True)
            if st.session_state.get("edit_org_id"):
                edit_id = st.session_state.edit_org_id
                org_to_edit = s.query(Organization).filter_by(id=edit_id).first()
                if org_to_edit:
                    st.markdown("#### Edit Organization")
                    new_name = st.text_input("Edit Organization Name", value=org_to_edit.name, key=f"edit_name_{edit_id}")
                    if st.button("💾 Save Changes", key=f"save_edit_{edit_id}"):
                        if new_name:
                            org_to_edit.name = new_name
                            s.commit()
                            st.success("Organization updated successfully.")
                            st.session_state.edit_org_id = None
                            safe_rerun()
            if st.session_state.get("delete_org_id"):
                del_id = st.session_state.delete_org_id
                org_to_delete = s.query(Organization).filter_by(id=del_id).first()
                if org_to_delete:
                    if st.button(f"✅ Confirm Delete {org_to_delete.name}", key=f"confirm_del_{del_id}"):
                        try:
                            s.delete(org_to_delete)
                            s.commit()
                            st.success(f"Organization '{org_to_delete.name}' deleted.")
                            st.session_state.delete_org_id = None
                            safe_rerun()
                        except Exception as e:
                            s.rollback()
                            st.error(f"Failed to delete organization: {e}")
    finally:
        s.close()
