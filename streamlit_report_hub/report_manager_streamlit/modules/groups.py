import streamlit as st
from db import SessionLocal
from models import Group, User
from .utils import safe_rerun

def group_management_page():
    st.header("👥 Groups Management")
    s = SessionLocal()
    try:
        org_id = st.session_state.user.get("organization_id")
        role = st.session_state.user.get("role_name")

        if not org_id:
            st.error("⚠️ No organization assigned.")
            return

        # Only Admins can create groups
        if role == "Admin":
            with st.expander("➕ Create New Group", expanded=True):
                with st.form("create_group_form"):
                    name = st.text_input("Group Name")
                    submitted = st.form_submit_button("Create Group")
                    if submitted:
                        if not name:
                            st.error("Please provide a group name.")
                        else:
                            g = Group(name=name, organization_id=org_id)
                            s.add(g)
                            s.commit()
                            st.success(f"Group '{name}' created successfully! 🎉")
                            safe_rerun()

        # List existing groups
        st.subheader("📋 Existing Groups")
        groups = s.query(Group).filter_by(organization_id=org_id).all()

        if not groups:
            st.info("No groups exist in your organization yet.")
            return

        for g in groups:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{g.name}** (ID: {g.id})")
                    member_names = [u.full_name for u in g.users]
                    st.caption(f"Members: {', '.join(member_names) if member_names else 'No members yet'}")
                with col2:
                    if role == "Admin" and st.button(f"Manage Members", key=f"manage_{g.id}"):
                        st.session_state.selected_group_id = g.id

        # Show manage UI only for selected group (Admins only)
        if role == "Admin" and st.session_state.get("selected_group_id"):
            st.markdown("---")
            manage_group_members(st.session_state.selected_group_id)

    finally:
        s.close()


def manage_group_members(group_id):
    """Admins assign users from their organization to this group."""
    st.subheader("🛠️ Manage Group Members")
    s = SessionLocal()
    try:
        group = s.query(Group).filter_by(id=group_id).first()
        if not group:
            st.error("Group not found.")
            return

        st.markdown(f"**Group:** {group.name}")

        # Only users from the same organization can be assigned
        users = get_users_in_org(group.organization_id)
        user_options = {u.full_name: u for u in users}
        pre_selected = [u.full_name for u in group.users]

        selected = st.multiselect(
            "Select Members",
            options=list(user_options.keys()),
            default=pre_selected
        )

        if st.button("💾 Save Members"):
            group.users = [user_options[name] for name in selected]
            s.commit()
            st.success("Members updated successfully! ✅")
            safe_rerun()

    finally:
        s.close()


@st.cache_data
def get_users_in_org(org_id):
    s = SessionLocal()
    try:
        return s.query(User).filter_by(organization_id=org_id).all()
    finally:
        s.close()
