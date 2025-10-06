import streamlit as st
import pandas as pd
import plotly.express as px
from db import SessionLocal
from models import Dashboard, Visualization, DashboardPermission, User, Group, Report, ReportPermission, group_members
from .utils import safe_rerun
from streamlit_sortables import sort_items
import uuid
import json
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

# -----------------------------
# Chart Builder (Sidebar)
# -----------------------------
def dashboards_builder(session, org_id, dashboard_id, user_id):
    """Sidebar builder for creating/editing visualizations (inspired by Looker Studio's data panel)."""
    st.sidebar.header("Chart Builder")

    db_user = session.query(User).filter_by(id=user_id).first()
    user_groups = [g.id for g in db_user.groups] if db_user else []
    reports = (
    session.query(Report)
    .filter(
        or_(
            Report.owner_id == user_id,
            Report.id.in_(
                session.query(ReportPermission.report_id)
                .filter(
                    or_(
                        ReportPermission.user_id == user_id,
                        ReportPermission.group_id.in_(user_groups)
                    )
                )
            )
        )
    ).all()
)

    if not reports:
        st.sidebar.info("No datasets available. Please upload a report first or request access.")
        return

    # Data source picker section, reloads dataframe/columns per selection
    report_options = {r.filename: r for r in reports}
    previous_report_id = st.session_state.get("chart_last_report_id")
    selected_report_name = st.sidebar.selectbox(
        "Choose Dataset", 
        list(report_options.keys()), 
        key=f"chart_ds_{dashboard_id}"
        )
    report = report_options.get(selected_report_name)
    
    if not report:
        return 
    
    # If report changed, reset session state and rerun
    dataset_widget_key = f"chart_ds_{dashboard_id}"
    
    current_selection = st.session_state.get(dataset_widget_key)
    previous_selection = st.session_state.get(f"{dataset_widget_key}_prev")
    if previous_selection is not None and current_selection != previous_selection:
        for key in [
            "chart_last_report_id",
            "chart_categorical_cols",
            "chart_numeric_cols",
            "chart_all_cols",
        ]:
            st.session_state.pop(key, None)
        st.session_state[f"{dataset_widget_key}_prev"] = current_selection
        safe_rerun()
        st.stop()
    else:
        #update stored selection for next time
        st.session_state[f"{dataset_widget_key}_prev"] = current_selection 
    
        

    # Permission check for selected report
    if not has_report_permission(session, report.id, user_id):
        st.sidebar.error("You do not have permission to use this report.")
        return

    # Only reload df and columns if the report changes
    if "chart_last_report_id" not in st.session_state or st.session_state["chart_last_report_id"] != report.id:
        df = load_report_dataframe(session, report.id)
        if df is None or df.empty:
            st.sidebar.warning("Dataset is empty or could not be loaded.")
            return
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category", "datetime64"]).columns.tolist()
        all_cols = categorical_cols + numeric_cols
        st.session_state["chart_last_report_id"] = report.id
        st.session_state["chart_numeric_cols"] = numeric_cols
        st.session_state["chart_categorical_cols"] = categorical_cols
        st.session_state["chart_all_cols"] = all_cols
    else:
        numeric_cols = st.session_state.get("chart_numeric_cols", [])
        categorical_cols = st.session_state.get("chart_categorical_cols", [])
        all_cols = st.session_state.get("chart_all_cols", [])

    chart_type = st.sidebar.selectbox("Chart Type", ["Bar", "Line", "Pie", "Scatter", "Area", "Table"])

    # Visualization title
    viz_title = st.sidebar.text_input("Visualization Title", value="New Visualization")

    config = {"report_id": report.id, "filters": {}}

    # Drag-and-drop logic or selectboxes
    color_by = None
    x = None
    y = None
    category = None
    values = None
    table_columns = []

    if all_cols:
        if chart_type in ["Bar", "Line", "Scatter", "Area"]:
            initial_containers = [
                {'header': 'Available Fields', 'items': all_cols},
                {'header': 'X-Axis', 'items': []},
                {'header': 'Y-Axis', 'items': []}
            ]
            sorted_containers = sort_items(
                initial_containers,
                multi_containers=True,
                key=f"fields_{dashboard_id}_{chart_type}_{report.id}"  # 👈 include report.id
            )
            x = sorted_containers[1]['items'][0] if sorted_containers[1]['items'] else None
            y = sorted_containers[2]['items'][0] if sorted_containers[2]['items'] else None
            if len(sorted_containers[1]['items']) > 1 or len(sorted_containers[2]['items']) > 1:
                st.sidebar.warning("Only the first item in X-Axis and Y-Axis will be used. Drag extras back to Available Fields.")

            color_options = ["None"] + categorical_cols
            color_by = st.sidebar.selectbox("Color By", color_options, index=0)
            if color_by == "None":
                color_by = None
            config.update({"x": x, "y": y, "color": color_by})

        elif chart_type == "Pie":
            initial_containers = [
                {'header': 'Available Fields', 'items': all_cols},
                {'header': 'Category', 'items': []},
                {'header': 'Values', 'items': []}
            ]
            sorted_containers = sort_items(
    initial_containers,
    multi_containers=True,
    key=f"fields_{dashboard_id}_{chart_type}_{report.id}"  # 👈 include report.id
)
            category = sorted_containers[1]['items'][0] if sorted_containers[1]['items'] else None
            values = sorted_containers[2]['items'][0] if sorted_containers[2]['items'] else None
            if len(sorted_containers[1]['items']) > 1 or len(sorted_containers[2]['items']) > 1:
                st.sidebar.warning("Only the first item in Category and Values will be used. Drag extras back to Available Fields.")
            config.update({"names": category, "values": values})

        elif chart_type == "Table":
            initial_containers = [
                {'header': 'Available Fields', 'items': all_cols},
                {'header': 'Selected Columns', 'items': []}
            ]
            sorted_containers = sort_items(
    initial_containers,
    multi_containers=True,
    key=f"fields_{dashboard_id}_{chart_type}_{report.id}"  # 👈 include report.id
)
            table_columns = sorted_containers[1]['items']
            config.update({"columns": table_columns})

    # Basic Filters
    st.sidebar.markdown("### Filters")
    filter_col = st.sidebar.selectbox("Filter Column", ["None"] + all_cols)
    if filter_col != "None":
        if filter_col in numeric_cols:
            min_val, max_val = st.sidebar.slider(
                f"Range for {filter_col}",
                float(df[filter_col].min()),
                float(df[filter_col].max()),
                (float(df[filter_col].min()), float(df[filter_col].max()))
            )
            config["filters"][filter_col] = [min_val, max_val]
        elif filter_col in categorical_cols:
            options = df[filter_col].unique().tolist()
            selected = st.sidebar.multiselect(f"Select values for {filter_col}", options, default=options[:5])
            config["filters"][filter_col] = selected

    # Preview and Save
    if st.sidebar.button("Preview & Add to Dashboard"):
        if not viz_title:
            st.sidebar.error("Please provide a visualization title.")
            return
        if chart_type in ["Bar", "Line", "Scatter", "Area"] and (not x or not y):
            st.sidebar.error("Please assign fields to both X-Axis and Y-Axis.")
            return
        if chart_type == "Pie" and (not category or not values):
            st.sidebar.error("Please assign fields to both Category and Values.")
            return
        if chart_type == "Table" and not table_columns:
            st.sidebar.error("Please select at least one column for the table.")
            return
        viz = Visualization(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            title=viz_title,
            type=chart_type,
            data_config=json.dumps(config),
            position=session.query(Visualization).filter_by(dashboard_id=dashboard_id).count()
        )
        session.add(viz)
        session.commit()
        st.sidebar.success("Visualization added!")
        safe_rerun()

# -----------------------------
# Dashboard Preview (Main Area - Grid Layout)
# -----------------------------
def dashboards_preview(session, dashboard_id):
    """Main area: Show visualizations in a 2-column grid layout to mimic a canvas."""
    st.header("Dashboard Canvas")

    visualizations = session.query(Visualization).filter_by(dashboard_id=dashboard_id).order_by(Visualization.position).all()
    if not visualizations:
        st.info("No visualizations yet. Use the sidebar to add one.")
        return

    # Drag-and-drop reordering (only for Editors/Admins/Owners)
    user_id = st.session_state.user["id"]
    role_name = st.session_state.user.get("role_name")
    dashboard = session.query(Dashboard).filter_by(id=dashboard_id).first()
    can_edit = role_name == "Admin" or dashboard.created_by_id == user_id or has_dashboard_permission(session, dashboard_id, user_id, "Editor")
    
    if can_edit:
        viz_titles = [v.title for v in visualizations]
        new_order = sort_items(viz_titles, key=f"order_{dashboard_id}", direction="horizontal")
        if new_order != viz_titles:
            for idx, title in enumerate(new_order):
                viz = next(v for v in visualizations if v.title == title)
                viz.position = idx
            session.commit()
            safe_rerun()

    # Render in 2-column grid
    cols = st.columns(2)
    for idx, viz in enumerate(visualizations):
        with cols[idx % 2]:
            render_visualization(session, viz)
            if can_edit:
                edit_delete_viz(session, viz)

# -----------------------------
# Share Dashboard
# -----------------------------
def share_dashboard(session, dashboard_id, user_id, selected_users, selected_groups, level):
    """Update dashboard permissions for selected users and groups. Also grant necessary report permissions."""
    dashboard = (
        session.query(Dashboard)
        .options(selectinload(Dashboard.visualizations))
        .filter_by(id=dashboard_id)
        .first()
        )
    if not dashboard:
        raise ValueError("Dashboard not found.")

    user_options = {
        u.full_name: u.id for u in session.query(User)
        .filter_by(organization_id=dashboard.organization_id)
        .filter(User.id != user_id).all()
    }
    group_options = {
        g.name: g.id for g in session.query(Group)
        .filter_by(organization_id=dashboard.organization_id).all()
    }

    # Remove any previous dashboard permissions for this dashboard
    session.query(DashboardPermission).filter_by(dashboard_id=dashboard_id).delete()

    # Set new dashboard permissions
    new_user_ids = []
    for name in selected_users:
        if name in user_options:
            uid = user_options[name]
            new_user_ids.append(uid)
            perm = DashboardPermission(
                id=str(uuid.uuid4()),
                dashboard_id=dashboard_id,
                user_id=uid,
                level=level
            )
            session.add(perm)
    new_group_ids = []
    for name in selected_groups:
        if name in group_options:
            gid = group_options[name]
            new_group_ids.append(gid)
            perm = DashboardPermission(
                id=str(uuid.uuid4()),
                dashboard_id=dashboard_id,
                group_id=gid,
                level=level
            )
            session.add(perm)
    session.commit()

    # --- GRANT REPORT PERMISSIONS TO USERS/GROUPS ---
    # Find all report_ids used by this dashboard
    dashboard_reports = set()
    for viz in getattr(dashboard, "visualizations", []):
        config = json.loads(viz.data_config)
        report_id = config.get("report_id")

        if report_id:
            dashboard_reports.add(report_id)

    # For each report in the dashboard, grant Viewer permission to each shared user/group if they don't already have permission
    for report_id in dashboard_reports:
        # Users
        for uid in new_user_ids:
            existing_perm = session.query(ReportPermission).filter_by(report_id=report_id, user_id=uid).first()
            if not existing_perm:
                perm = ReportPermission(
                    id=str(uuid.uuid4()),
                    report_id=report_id,
                    user_id=uid,
                    level="Viewer"
                )
                session.add(perm)
        # Groups
        for gid in new_group_ids:
            existing_perm = session.query(ReportPermission).filter_by(report_id=report_id, group_id=gid).first()
            if not existing_perm:
                perm = ReportPermission(
                    id=str(uuid.uuid4()),
                    report_id=report_id,
                    group_id=gid,
                    level="Viewer"
                )
                session.add(perm)
    session.commit()

# -----------------------------
# Helper: Check Dashboard Permission
# -----------------------------
def has_dashboard_permission(session, dashboard_id, user_id, required_level=None):
    dashboard = session.query(Dashboard).filter_by(id=dashboard_id).first()
    if not dashboard:
        return False

    # Owner always has access
    if dashboard.created_by_id == user_id:
        return True

    # Optionally allow admins full access
    if "user" in st.session_state and st.session_state.user.get("role_name") == "Admin":
        return True

    db_user = session.query(User).filter_by(id=user_id).first()
    user_groups = [g.id for g in db_user.groups] if db_user else []

    perm = (
        session.query(DashboardPermission)
        .filter_by(dashboard_id=dashboard_id)
        .filter(
            or_(
                DashboardPermission.user_id == user_id,
                DashboardPermission.group_id.in_(user_groups)
            )
        )
        .first()
    )

    if not perm:
        return False

    if required_level:
        return perm.level == required_level
    return True

# -----------------------------
# Helper: Check Report Permission
# -----------------------------
def has_report_permission(session, report_id, user_id):
    """Check if user has at least 'Viewer' permission for the report (direct or group) or is owner."""
    report = session.query(Report).filter_by(id=report_id).first()
    if not report:
        return False
    if report.owner_id == user_id:
        return True
    db_user = session.query(User).filter_by(id=user_id).first()
    user_groups = [g.id for g in db_user.groups] if db_user else []
    perm = (
        session.query(ReportPermission)
        .filter_by(report_id=report_id)
        .filter(
            or_(
                ReportPermission.user_id == user_id,
                ReportPermission.group_id.in_(user_groups)
            )
        )
        .first()
    )
    if perm:
        return perm.level in ["Viewer", "Commenter", "Editor", "Owner"]
    return False

# -----------------------------
# Render Single Visualization
# -----------------------------
def render_visualization(session, viz):
    config = json.loads(viz.data_config)
    df = load_report_dataframe(session, config["report_id"])
    if df is None:
        st.warning(f"Data not found for {viz.title}")
        return

    # Apply filters
    filters = config.get("filters", {})
    for col, vals in filters.items():
        if col in df.columns:
            if df[col].dtype in ["int64", "float64"]:
                df = df[(df[col] >= vals[0]) & (df[col] <= vals[1])]
            else:
                df = df[df[col].isin(vals)]

    st.markdown(f"**{viz.title}** ({viz.type})")

    if viz.type == "Bar":
        fig = px.bar(df, x=config.get("x"), y=config.get("y"), color=config.get("color"))
        st.plotly_chart(fig, use_container_width=True)
    elif viz.type == "Line":
        fig = px.line(df, x=config.get("x"), y=config.get("y"), color=config.get("color"))
        st.plotly_chart(fig, use_container_width=True)
    elif viz.type == "Scatter":
        fig = px.scatter(df, x=config.get("x"), y=config.get("y"), color=config.get("color"))
        st.plotly_chart(fig, use_container_width=True)
    elif viz.type == "Area":
        fig = px.area(df, x=config.get("x"), y=config.get("y"), color=config.get("color"))
        st.plotly_chart(fig, use_container_width=True)
    elif viz.type == "Pie":
        fig = px.pie(df, names=config.get("names"), values=config.get("values"))
        st.plotly_chart(fig, use_container_width=True)
    elif viz.type == "Table":
        st.dataframe(df[config.get("columns", df.columns.tolist())])

# -----------------------------
# Load DataFrame Helper (with Permission Check)
# -----------------------------
def load_report_dataframe(session, report_id):
    report = session.query(Report).filter_by(id=report_id).first()
    if report:
        user_id = st.session_state.user["id"]
        if not has_report_permission(session, report_id, user_id):
            st.error("You do not have permission to view this report.")
            return None
        try:
            if report.filename.endswith(".csv"):
                return pd.read_csv(report.filepath)
            elif report.filename.endswith(".xlsx"):
                return pd.read_excel(report.filepath)
        except Exception as e:
            st.error(f"Failed to load report data: {e}")
            return None
    return None

# -----------------------------
# Edit/Delete Viz
# -----------------------------
def edit_delete_viz(session, viz):
    with st.expander(f"Edit/Delete: {viz.title}"):
        config = json.loads(viz.data_config)
        df = load_report_dataframe(session, config["report_id"])
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist() if df is not None else []
        categorical_cols = df.select_dtypes(include=["object", "category", "datetime64"]).columns.tolist() if df is not None else []
        all_cols = categorical_cols + numeric_cols

        new_title = st.text_input("Title", viz.title, key=f"edit_title_{viz.id}")
        new_type = st.selectbox("Type", ["Bar", "Line", "Pie", "Scatter", "Area", "Table"],
                                index=["Bar", "Line", "Pie", "Scatter", "Area", "Table"].index(viz.type),
                                key=f"edit_type_{viz.id}")

        # Drag-and-drop for editing with multi-containers
        color_by = config.get("color")
        x = config.get("x") or config.get("names")
        y = config.get("y") or config.get("values")
        table_columns = config.get("columns", [])

        if new_type in ["Bar", "Line", "Scatter", "Area"]:
            initial_containers = [
                {'header': 'Available Fields', 'items': [c for c in all_cols if c not in [x, y]]},
                {'header': 'X-Axis', 'items': [x] if x else []},
                {'header': 'Y-Axis', 'items': [y] if y else []}
            ]
            sorted_containers = sort_items(initial_containers, multi_containers=True, key=f"edit_fields_{viz.id}_{new_type}")
            x = sorted_containers[1]['items'][0] if sorted_containers[1]['items'] else None
            y = sorted_containers[2]['items'][0] if sorted_containers[2]['items'] else None
            if len(sorted_containers[1]['items']) > 1 or len(sorted_containers[2]['items']) > 1:
                st.warning("Only the first item in X-Axis and Y-Axis will be used. Drag extras back to Available Fields.")

            color_options = ["None"] + categorical_cols
            color_by = st.selectbox("Color By", color_options,
                                    index=color_options.index(color_by) if color_by in color_options else 0,
                                    key=f"edit_color_{viz.id}")
            if color_by == "None":
                color_by = None

        elif new_type == "Pie":
            initial_containers = [
                {'header': 'Available Fields', 'items': [c for c in all_cols if c not in [x, y]]},
                {'header': 'Category', 'items': [x] if x else []},
                {'header': 'Values', 'items': [y] if y else []}
            ]
            sorted_containers = sort_items(initial_containers, multi_containers=True, key=f"edit_fields_{viz.id}_{new_type}")
            x = sorted_containers[1]['items'][0] if sorted_containers[1]['items'] else None  # Reuse x for category
            y = sorted_containers[2]['items'][0] if sorted_containers[2]['items'] else None  # Reuse y for values
            if len(sorted_containers[1]['items']) > 1 or len(sorted_containers[2]['items']) > 1:
                st.warning("Only the first item in Category and Values will be used. Drag extras back to Available Fields.")

        elif new_type == "Table":
            initial_containers = [
                {'header': 'Available Fields', 'items': [c for c in all_cols if c not in table_columns]},
                {'header': 'Selected Columns', 'items': table_columns}
            ]
            sorted_containers = sort_items(initial_containers, multi_containers=True, key=f"edit_fields_{viz.id}_{new_type}")
            table_columns = sorted_containers[1]['items']

        # Filters (simplified, can expand to match builder)
        st.markdown("**Filters**")
        filter_col = st.selectbox("Filter Column", ["None"] + all_cols, key=f"edit_filter_col_{viz.id}")
        if filter_col != "None":
            if filter_col in numeric_cols:
                min_val, max_val = st.slider(
                    f"Range for {filter_col}",
                    float(df[filter_col].min()),
                    float(df[filter_col].max()),
                    (float(config["filters"].get(filter_col, [df[filter_col].min(), df[filter_col].max()])[0]),
                     float(config["filters"].get(filter_col, [df[filter_col].min(), df[filter_col].max()])[1])),
                    key=f"edit_filter_range_{viz.id}"
                )
                config["filters"][filter_col] = [min_val, max_val]
            elif filter_col in categorical_cols:
                options = df[filter_col].unique().tolist()
                selected = st.multiselect(f"Select values for {filter_col}", options,
                                         default=config["filters"].get(filter_col, options[:5]),
                                         key=f"edit_filter_values_{viz.id}")
                config["filters"][filter_col] = selected

        if st.button("Update", key=f"update_{viz.id}"):
            viz.title = new_title
            viz.type = new_type
            new_config = {"report_id": config["report_id"], "filters": config["filters"]}
            if new_type in ["Bar", "Line", "Scatter", "Area"]:
                new_config.update({"x": x, "y": y, "color": color_by})
            elif new_type == "Pie":
                new_config.update({"names": x, "values": y})
            elif new_type == "Table":
                new_config.update({"columns": table_columns})
            viz.data_config = json.dumps(new_config)
            session.commit()
            st.success("Visualization updated!")
            safe_rerun()

        if st.button("Delete", key=f"delete_{viz.id}"):
            session.delete(viz)
            session.commit()
            st.success("Visualization deleted!")
            safe_rerun()