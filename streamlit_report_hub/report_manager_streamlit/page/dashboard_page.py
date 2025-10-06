def dashboards_main_page():
    """Main entry point for the dashboards section, Looker Studio-style, gorgeous icons and all."""
    import os, uuid, json
    import pandas as pd
    from sqlalchemy import or_
    from db import SessionLocal
    from models import User, Group, Report, Dashboard, Visualization, DashboardPermission, group_members
    from modules.dashboards import dashboards_builder, dashboards_preview, has_dashboard_permission, share_dashboard
    import streamlit as st 
    from modules.utils import safe_rerun 
    

    st.set_page_config(layout="wide", page_title="Analytics", page_icon="fa-solid fa-chart-line")
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
        <style>
            .builder-card {
                background: #f5f6f8;
                border-radius: 12px;
                padding: 24px 30px 20px 30px;
                margin-bottom: 26px;
                display: flex;
                gap: 18px;
                align-items: flex-start;
                border: 1px solid #ecedf3;
            }
            .builder-icon {
                font-size: 2.2em;
                color: #6d74d6;
                background: #eaeafc;
                border-radius: 10px;
                padding: 18px;
                margin-right: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 56px;width:56px;
            }
            .builder-title {font-weight: bold; font-size: 1.1em;}
            .builder-meta {color: #7e8899; font-size: 1em;}
            .builder-tag {
                display: inline-block;
                background: #f4f8fe;
                color: #2460a8;
                border-radius: 7px;
                font-size: .92em;
                padding: 3px 12px;
                margin-right: 6px;
                margin-top:7px;
            }
            .datasource-card {display:flex;align-items:center;gap:16px;background:#fff;border:1.5px solid #f0f2f5;
                border-radius:10px;padding:20px 18px 12px 18px;margin-bottom:13px;}
            .datasource-icon {font-size:2.2em;color:#4b778d;background:#f4f8ff;border-radius:9px;padding:9px;margin-right:14px;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<a href="#" style="color:#49506f; text-decoration:none;"><i class="fa-solid fa-chevron-left"></i> Back</a>', unsafe_allow_html=True)
    st.markdown('## Create Analytics Dashboard')
    st.caption("Select a data source to create visualizations and dashboards")

    st.markdown("""
      <div class="builder-card">
        <div class="builder-icon">
          <i class="fa-solid fa-chart-line"></i>
        </div>
        <div>
          <div class="builder-title">Dashboard Builder</div>
          <div class="builder-meta">Transform your data into interactive visualizations. Only reports with structured data (CSV, Excel) can be used to create dashboards.</div>
          <div style="margin-top:7px;">
            <span class="builder-tag"><i class="fa-solid fa-database"></i> CSV Support</span>
            <span class="builder-tag"><i class="fa-solid fa-file-excel"></i> Excel Support</span>
            <span class="builder-tag"><i class="fa-solid fa-chart-simple"></i> Interactive Charts</span>
          </div>
        </div>
      </div>
    """, unsafe_allow_html=True)
    search_term = st.text_input("Search data sources...", key="analytics_search")

    st.markdown("""
        <div style="font-weight:600;font-size:1.18em;margin-bottom:9px;margin-top:10px;">
          Available Data Sources
        </div>
        <div style="font-size:0.98em;color:#7e8899;margin-bottom:14px;">
          Reports with structured data that can be used for analytics
        </div>
    """, unsafe_allow_html=True)

    if "user" not in st.session_state or not st.session_state.get("authenticated"):
        st.warning("Please log in to access dashboards.")
        return

    user = st.session_state.user
    user_id = user["id"]
    role_name = user.get("role_name")

    if role_name == "Superadmin":
        st.info("Superadmins focus on system management and do not manage dashboards or reports.")
        return

    org_id = user.get("organization_id")
    if not org_id:
        st.error("You are not assigned to any organization.")
        return

    session = SessionLocal()
    try:
        analytics_reports = (
            session.query(Report)
            .filter(
                Report.organization_id == org_id,
                or_(
                    Report.filename.ilike("%.csv"),
                    Report.filename.ilike("%.xlsx"),
                    Report.filename.ilike("%.xls")
                )
            )
            .all()
        )
        if search_term:
            analytics_reports = [
                r for r in analytics_reports if search_term.lower() in r.title.lower() or search_term.lower() in r.filename.lower()
            ]
        if not analytics_reports:
            st.info("No eligible data sources found.")
        else:
            for r in analytics_reports:
                ext = r.filename.split(".")[-1].lower()
                icon_map = {'csv': 'fa-file-csv', 'xlsx': 'fa-file-excel', 'xls': 'fa-file-excel'}
                fa_icon = icon_map.get(ext, 'fa-database')
                owner = session.query(User).filter_by(id=r.owner_id).first()
                uploader_name = owner.full_name if owner else "Unknown"
                date_str = r.created_at.strftime('%Y-%m-%d')
                size_bytes = os.path.getsize(r.filepath)
                size_str = f"{size_bytes/1024:.0f} KB" if size_bytes < 1024*1024 else f"{size_bytes/1024/1024:.1f} MB"
                tag_str = f"<span style='background:#dcffe4;color:#178548;border-radius:5px;padding:3px 11px;font-size:.93em;margin-left:7px;'><i class='fa-solid fa-database'></i> Data Source</span>"
                ext_tag = f"<span style='background:#e7f3ff;color:#255a93;border-radius:4px;font-size:.95em;padding:2px 7px;margin-left:5px;'>{ext.upper()}</span>"

                st.markdown(f"""
                <div class="datasource-card">
                    <i class="fa-solid {fa_icon} datasource-icon"></i>
                    <div style="flex:1;">
                      <div style="font-weight:500;font-size:1.09em;">{r.title} {ext_tag} {tag_str}</div>
                      <div style="color:#8c97a9;font-size:.96em;margin-top:3px;">
                          <i class="fa-regular fa-user"></i> {uploader_name} &nbsp; 
                          <i class="fa-regular fa-calendar"></i> {date_str} &nbsp; 
                          <i class="fa-solid fa-database"></i> {size_str}
                      </div>
                    </div>
                    <div>
                      {st.button("Create Dashboard", key=f"create_dashboard_{r.id}")}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                # Button logic: set form state and rerun
                if st.session_state.get(f"create_dashboard_{r.id}"):
                    st.session_state["dashboard_create_form_id"] = r.id
                    st.session_state["dashboard_create_default"] = f"Analytics from {r.title}"
                    safe_rerun()

        # Show dashboard creation form if requested
        if st.session_state.get("dashboard_create_form_id"):
            r_id = st.session_state["dashboard_create_form_id"]
            default_name = st.session_state.get("dashboard_create_default", "")
            report = next((item for item in analytics_reports if item.id == r_id), None)
            if report:
                with st.form("create_dash_from_ds_form"):
                    dash_name = st.text_input("Dashboard Name", value=default_name, key="analytics_dash_title")
                    dash_desc = st.text_area("Description (Optional)", key="analytics_dash_desc")
                    submit_col, cancel_col = st.columns(2)
                    with submit_col:
                        submitted = st.form_submit_button("Create Dashboard")
                    with cancel_col:
                        cancelled = st.form_submit_button("Cancel")
                    if submitted:
                        dash = Dashboard(
                            id=str(uuid.uuid4()),
                            name=dash_name,
                            description=dash_desc or "Created from data source.",
                            organization_id=org_id,
                            created_by_id=user_id,
                        )
                        session.add(dash)
                        session.commit()
                        st.success(f"Dashboard '{dash_name}' created!")
                        del st.session_state["dashboard_create_form_id"]
                        del st.session_state["dashboard_create_default"]
                        safe_rerun()
                    if cancelled:
                        del st.session_state["dashboard_create_form_id"]
                        del st.session_state["dashboard_create_default"]
                        safe_rerun()

        # -- Add any further dashboard selector, share, preview, and edit logic here as in your original code --
                # Refresh user from DB to access up-to-date groups relationship
        # Always get the up-to-date ORM user object!
        db_user = session.query(User).filter_by(id=user_id).first()
        # (Assume loaded db_user as current user object)
        user_groups = [g.id for g in db_user.groups] if db_user else []

        dashboards = (
            session.query(Dashboard)
            .filter(
                or_(
                    Dashboard.created_by_id == user_id,  # you are creator
                    Dashboard.id.in_(
                        session.query(DashboardPermission.dashboard_id)
                        .filter(
                            or_(
                                DashboardPermission.user_id == user_id,
                                DashboardPermission.group_id.in_(user_groups)
                            )
                        )
                    )
                )
            )
            .all()
        )


        dashboard_names = ["Select a Dashboard"] + [
            f"{d.name} (Shared)" if d.organization_id != org_id and d.created_by_id != user_id else d.name
            for d in dashboards
        ]
        selected_dashboard = st.selectbox(
            "Select a Dashboard",
            dashboard_names,
            key="dashboard_select",
            format_func=lambda name: f"📊 {name}" if name != "Select a Dashboard" else name
        )
        selected_dash = None
        if selected_dashboard != "Select a Dashboard":
            selected_dash = next(
                (d for d in dashboards if d.name == selected_dashboard.replace(" (Shared)", "")), None
            )

        # Dashboard actions
        icon_col1, icon_col2 = st.columns([1, 1])
        with icon_col1:
            can_create = role_name == "Admin" or not selected_dash or has_dashboard_permission(
                session, selected_dash.id if selected_dash else None, user_id, "Editor")
            if can_create and st.button("➕ New Dashboard", key="new_dashboard_btn"):
                st.session_state["show_create_form"] = True
        with icon_col2:
            if selected_dash and (role_name == "Admin" or selected_dash.created_by_id == user_id or has_dashboard_permission(
                session, selected_dash.id, user_id, "Editor")):
                if st.button("🔗 Share", key="share_btn"):
                    st.session_state["show_share_form"] = True

        # Create dashboard modal
        if st.session_state.get("show_create_form", False) and can_create:
            with st.form("create_dashboard_form"):
                name = st.text_input("Dashboard Name")
                desc = st.text_area("Description (Optional)")
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit = st.form_submit_button("Create")
                with col_cancel:
                    cancel = st.form_submit_button("Cancel")
                if submit:
                    if not name:
                        st.error("Dashboard name is required.")
                    elif any(d.name == name for d in dashboards):
                        st.error("A dashboard with this name already exists.")
                    else:
                        dash = Dashboard(
                            id=str(uuid.uuid4()),
                            name=name,
                            description=desc or "No description provided",
                            organization_id=org_id,
                            created_by_id=user["id"]
                        )
                        session.add(dash)
                        session.commit()
                        st.success(f"Dashboard '{name}' created!")
                        st.session_state["show_create_form"] = False
                        safe_rerun()
                if cancel:
                    st.session_state["show_create_form"] = False
                    safe_rerun()

        # Share dashboard modal
        if selected_dash and st.session_state.get("show_share_form", False) and (role_name == "Admin" or selected_dash.created_by_id == user_id or has_dashboard_permission(
            session, selected_dash.id, user_id, "Editor")):
            with st.form("share_dashboard_form"):
                st.subheader("Share Dashboard")
                users = session.query(User).filter_by(organization_id=selected_dash.organization_id).filter(
                    User.id != user['id']).all()
                groups = session.query(Group).filter_by(organization_id=selected_dash.organization_id).all()
                user_options = {u.full_name: u.id for u in users}
                group_options = {g.name: g.id for g in groups}
                selected_users = st.multiselect(
                    "Share with Users", list(user_options.keys()), key=f"share_users_{selected_dash.id}")
                selected_groups = st.multiselect(
                    "Share with Groups", list(group_options.keys()), key=f"share_groups_{selected_dash.id}")
                level = st.selectbox(
                    "Permission", ["Viewer", "Editor"], key=f"share_level_{selected_dash.id}"
                )

                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit = st.form_submit_button("Apply Sharing")
                with col_cancel:
                    cancel = st.form_submit_button("Cancel")

                if submit:
                    if not selected_users and not selected_groups:
                        st.error("Please select at least one user or group to share with.")
                    else:
                        try:
                            share_dashboard(session, selected_dash.id, user["id"], selected_users, selected_groups, level)
                            st.success("Sharing settings updated!")
                            st.session_state["show_share_form"] = False
                            safe_rerun()
                        except ValueError as e:
                            st.error(str(e))
                if cancel:
                    st.session_state["show_share_form"] = False
                    safe_rerun()

        # Dashboard preview and sidebar chart builder
        if selected_dash:
            can_edit = role_name == "Admin" or selected_dash.created_by_id == user_id or has_dashboard_permission(
                session, selected_dash.id, user_id, "Editor")
            if can_edit:
                with st.sidebar:
                    st.header("Chart Builder")
                    dashboards_builder(session, org_id, selected_dash.id, user_id)
            else:
                st.sidebar.info("You have Viewer access only. Editing is disabled.")
            dashboards_preview(session, selected_dash.id)
        else:
            st.info("Select or create a dashboard to start building visualizations.")


    finally:
        session.close()
