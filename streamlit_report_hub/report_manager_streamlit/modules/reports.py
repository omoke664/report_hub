import streamlit as st
from .utils import safe_rerun
from db import SessionLocal
import os
import pandas as pd
import io
from models import Report, User, Group, ReportPermission, group_members, Folder, Comment
from sqlalchemy import or_
import uuid
import base64

st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <style>
      .folder-card, .report-card { 
        background: #fff; 
        border-radius: 12px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); 
        padding: 19px 23px 14px 23px; 
        margin-bottom: 12px; 
        display: flex; 
        align-items: center;
        gap: 15px;
      }
      .folder-card:hover, .report-card:hover {box-shadow: 0 4.5px 16px 0 rgba(51,74,188,0.091);}
      .folder-icon {font-size: 1.8em; color: #535bff;}
      .report-icon {font-size: 1.6em; color: #232e71;}
      .card-title {font-weight:bold; font-size:1.09em;}
      .card-meta {color: #718093; font-size:.94em;}
      .action-btn {margin-left:auto;}
      .action-btn button {margin-left:8px;}
      .breadcrumb {margin-bottom:14px;font-weight:500;color:#7c848e;}
      .breadcrumb i {color:#888ac5;}
    </style>
""", unsafe_allow_html=True)



def reports_page():
    st.title("All Reports")
    st.caption("Manage and organize your organization's reports")
    
    user = st.session_state.user
    if user['role_name'] == 'Superadmin':
        st.info("Superadmins do not manage reports.")
        return
    
    s = SessionLocal()
    try:
        if 'current_folder' not in st.session_state:
            st.session_state.current_folder = None
        if 'show_upload' not in st.session_state:
            st.session_state.show_upload = False
        if 'show_new_folder' not in st.session_state:
            st.session_state.show_new_folder = False
        
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            search_term = st.text_input("Search reports, files, and folders...", key="report_search")
        with col2:
            type_filter = st.selectbox("Type", ["All Types", "PDF", "CSV", "XLSX", "PPTX"], key="type_filter")
        with col3:
            date_sort = st.selectbox("Sort by Date", ["Newest", "Oldest"], key="date_sort")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("New Folder"):
                st.session_state.show_new_folder = True
        with col_b:
            if st.button("Upload"):
                st.session_state.show_upload = True
        
        if st.session_state.show_new_folder:
            new_folder_form(s, user)
        
        if st.session_state.show_upload:
            report_upload_page(s, user)
        
        display_folders(s, user, search_term)
        
        if st.session_state.current_folder:
            folder = s.query(Folder).filter_by(id=st.session_state.current_folder).first()
            if folder:
                st.subheader(f"{folder.name} Folder")
            if st.button("Back to All Folders"):
                st.session_state.current_folder = None
                safe_rerun()
        
        reports = fetch_reports(s, user, st.session_state.current_folder)
        filtered_reports = filter_and_sort_reports(reports, search_term, type_filter, date_sort)
        
        st.subheader(f"Reports ({len(filtered_reports)} items)")
        for r in filtered_reports:
            display_report_item(s, user, r)
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
    finally:
        s.close()

def display_folders(s, user, search_term):
    org_id = user.get('organization_id', user.get('org_id'))
    if not org_id:
        st.error("Organization ID not found in user session.")
        return
    folders = s.query(Folder).filter_by(organization_id=org_id).all()
    filtered_folders = [f for f in folders if search_term.lower() in f.name.lower()] if search_term else folders
    folder_cols = st.columns(3)
    for i, f in enumerate(filtered_folders):
        count = s.query(Report).filter_by(folder_id=f.id).count()
        with folder_cols[i % 3]:
            st.markdown(
                f"""<div class="folder-card">
                <i class="fa-solid fa-folder folder-icon"></i>
                <div>
                  <div class="card-title">{f.name}</div>
                  <div class="card-meta">{count} reports</div>
                </div>
                <div class="action-btn">{st.button('Open', key=f"open_folder_{f.id}")}</div>
                </div>
                """, unsafe_allow_html=True)
            if st.session_state.get(f"open_folder_{f.id}"):
                st.session_state.current_folder = f.id
                st.session_state.show_new_folder = False
                safe_rerun()

def new_folder_form(s, user):
    org_id = user.get('organization_id', user.get('org_id'))
    if not org_id:
        st.error("Organization ID not found in user session.")
        return
    with st.form('new_folder'):
        name = st.text_input('Folder name', key='new_folder_name')
        submitted = st.form_submit_button('Create')
        if submitted:
            if not name:
                st.error('Please provide a name.')
                return
            # Check unique name in org
            exists = s.query(Folder).filter_by(name=name, organization_id=org_id).first()
            if exists:
                st.error("A folder with this name already exists.")
                return
            folder = Folder(
                id=str(uuid.uuid4()),
                name=name,
                organization_id=org_id,
            )
            s.add(folder)
            s.commit()
            st.success(f"Folder '{name}' created!")
            st.session_state.show_new_folder = False
            safe_rerun()


def report_upload_page(s, user):
    org_id = user.get('organization_id', user.get('org_id'))
    if not org_id:
        st.error("Organization ID not found in user session.")
        return
    folders = s.query(Folder).filter_by(organization_id=org_id).all()
    folder_options = {"None": None}
    folder_options.update({f.name: f.id for f in folders})
    
    with st.form('upload_report'):
        # Set the value before the widget is created, if you want an initial default
        if "report_title" not in st.session_state:
            st.session_state["report_title"] = "My Awesome Report"

        title = st.text_input("Report Title", key="report_title")

        uploaded_file = st.file_uploader('Choose a file', type=['pdf', 'csv', 'xlsx', 'pptx'], key='report_file')
        selected_folder = st.selectbox("Select folder (optional)", list(folder_options.keys()))
        submitted = st.form_submit_button('Upload')
        
        if submitted:
            if not uploaded_file or not title:
                st.error('Please provide a title and select a file.')
                return
            
            report_id = str(uuid.uuid4())
            os.makedirs(os.path.join('uploads', str(org_id)), exist_ok=True)
            filepath = os.path.join('uploads', str(org_id), f"{report_id}_{uploaded_file.name}")
            with open(filepath, 'wb') as f:
                f.write(uploaded_file.getbuffer())

            report = Report(
                id=report_id,
                title=title,
                filename=uploaded_file.name,
                filepath=filepath,
                owner_id=user['id'],
                organization_id=org_id,
                folder_id=folder_options[selected_folder]
            )
            s.add(report)
            perm = ReportPermission(
                id=str(uuid.uuid4()),
                report_id=report_id,
                user_id=user['id'],
                level='Owner'
            )
            s.add(perm)
            s.commit()
            
            st.success(f"Report '{title}' uploaded successfully! 📄")
            st.session_state.report_title = ""
            st.session_state.report_file = None
            st.session_state.show_upload = False
            safe_rerun()



def fetch_reports(s, user, folder_id):
    user_groups = [g.id for g in s.query(Group).join(group_members).filter(group_members.c.user_id == user['id']).all()]
    org_id = user.get('organization_id', user.get('org_id'))
    if not org_id:
        st.error("Organization ID not found in user session.")
        return []
    query = s.query(Report).filter(
        or_(
            Report.owner_id == user['id'],
            Report.organization_id == org_id,
            Report.id.in_(
                s.query(ReportPermission.report_id)
                .filter(
                    or_(
                        ReportPermission.user_id == user['id'],
                        ReportPermission.group_id.in_(user_groups)
                    )
                )
            )
        )
    )
    if folder_id:
        query = query.filter(Report.folder_id == folder_id)
    else:
        query = query.filter(Report.folder_id.is_(None))
    return query.all()

def filter_and_sort_reports(reports, search_term, type_filter, date_sort):
    filtered = [r for r in reports if search_term.lower() in r.title.lower() or search_term.lower() in r.filename.lower()]
    if type_filter != "All Types":
        ext_map = {"PDF": ".pdf", "CSV": ".csv", "XLSX": ".xlsx", "PPTX": ".pptx"}
        filtered = [r for r in filtered if r.filename.lower().endswith(ext_map[type_filter])]
    filtered.sort(key=lambda r: r.created_at, reverse=(date_sort == "Newest"))
    return filtered

def display_report_item(s, user, r):
    # File type to Font Awesome icon
    ext = r.filename.split('.')[-1].lower()
    icon_map = {
        'pdf': 'file-pdf', 'csv': 'file-csv', 'xlsx': 'file-excel', 'pptx': 'file-powerpoint'
    }
    fa_icon = icon_map.get(ext, 'file-lines')

    owner = s.query(User).filter_by(id=r.owner_id).first()
    uploader_name = owner.full_name if owner else r.owner_id
    size = os.path.getsize(r.filepath) / 1024
    size_str = f"{size:.1f} KB" if size < 1024 else f"{size/1024:.1f} MB"
    date_str = r.created_at.strftime('%Y-%m-%d')
    level = get_effective_permission(user['id'], r)
    color = {'Viewer': '#e2e8f0', 'Commenter': '#ffeb8a', 'Editor': '#a7e1fa', 'Owner': '#6ee7b7'}.get(level, '#eeeeee')
    badge = f"""<span style="background-color:{color};
        color:#1c2129;font-weight:500;padding:5px 11px;border-radius:7px;font-size:13px;margin-left:6px;">
        <i class="fa-solid fa-key"></i> {level.capitalize()}
    </span>"""

    st.markdown(
        f"""
        <div class="report-card">
            <i class="fa-solid fa-{fa_icon} report-icon"></i>
            <div>
                <div class="card-title" style='margin-bottom:2px;'>{r.title}</div>
                <div class="card-meta">{r.filename} · <i class="fa-solid fa-database"></i> {size_str}</div>
                <div class="card-meta"><i class="fa-regular fa-user"></i> {uploader_name} · <i class="fa-regular fa-calendar"></i> {date_str}</div>
            </div>
            <div style="margin-left:auto;">
                {badge}
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    with st.expander("Details"):
        # View/Download section
        if ext in ("csv", "xlsx"):
            df = pd.read_csv(r.filepath) if ext == "csv" else pd.read_excel(io.BytesIO(open(r.filepath, 'rb').read()))
            if level in ['Editor', 'Owner']:
                mode = st.selectbox("Mode", ["View", "Edit"], key=f"mode_{r.id}")
                if mode == "View":
                    st.dataframe(df, use_container_width=True)
                else:
                    edited_df = st.data_editor(df, use_container_width=True, key=f"editor_{r.id}")
                    if st.button("Save Changes", key=f"save_{r.id}"):
                        save_file(edited_df, r.filepath)
                        st.success("Changes saved!")
            else:
                st.subheader("View")
                st.dataframe(df, use_container_width=True)
        elif ext == "pdf":
            with open(r.filepath, "rb") as f:
                pdf_bytes = f.read()
            st.subheader("View PDF")
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.subheader("Download")
            with open(r.filepath, 'rb') as f:
                st.download_button(
                    label="Download <i class='fa-solid fa-download'></i>",
                    data=f,
                    file_name=r.filename,
                    mime="application/octet-stream",
                )

        # Comment section
        if level in ['Commenter', 'Editor', 'Owner']:
            st.subheader("Add Comment")
            comment = st.text_area("Your comment", key=f"comment_{r.id}")
            if st.button("Submit Comment", key=f"submit_comment_{r.id}"):
                save_comment(s, r.id, user['id'], comment)
                st.success("Comment added!")
            st.subheader("Comments")
            display_comments(s, r.id)

        # Move to folder
        if level in ['Editor', 'Owner']:
            org_id = user.get('organization_id', user.get('org_id'))
            folders = s.query(Folder).filter_by(organization_id=org_id).all()
            folder_options = ["None"] + [f.name for f in folders]
            current_folder_name = next((f.name for f in folders if f.id == r.folder_id), "None")
            selected_folder = st.selectbox("Move to folder", folder_options, index=folder_options.index(current_folder_name), key=f"move_select_{r.id}")
            if selected_folder != current_folder_name:
                if st.button("Move Report", key=f"move_{r.id}"):
                    new_folder_id = next((f.id for f in folders if f.name == selected_folder), None)
                    r.folder_id = new_folder_id
                    s.commit()
                    st.success(f"Moved to {selected_folder}!")
                    safe_rerun()

        # Manage permissions
        if level in ['Editor', 'Owner']:
            if st.button("Manage Permissions", key=f"perm_{r.id}"):
                st.session_state[f"manage_perm_{r.id}"] = True
            if st.session_state.get(f"manage_perm_{r.id}", False):
                assign_report_permissions(s, user, r.id, level)
                if st.button("Close Permissions", key=f"close_perm_{r.id}"):
                    st.session_state[f"manage_perm_{r.id}"] = False

        # Delete (only for Owner)
        if level == 'Owner':
            if st.button("Delete Report", key=f"delete_{r.id}"):
                delete_report(s, r.id)
                st.success("Report deleted!")
                safe_rerun()

def get_effective_permission(user_id, report):
    if report.owner_id == user_id:
        return "Owner"
    
    s = SessionLocal()
    try:
        direct = s.query(ReportPermission).filter_by(report_id=report.id, user_id=user_id).first()
        direct_level = direct.level if direct else None
        
        user_groups = [g.id for g in s.query(Group).join(group_members).filter(group_members.c.user_id == user_id).all()]
        group_perms = s.query(ReportPermission).filter(ReportPermission.report_id == report.id, ReportPermission.group_id.in_(user_groups)).all()
        group_levels = [p.level for p in group_perms]
        
        all_levels = [lvl for lvl in [direct_level] + group_levels if lvl]
        if not all_levels:
            return "Viewer" if report.organization_id == st.session_state.user.get('organization_id', st.session_state.user.get('org_id')) else None
        
        order = {"Viewer": 1, "Commenter": 2, "Editor": 3, "Owner": 4}
        return max(all_levels, key=lambda l: order[l])
    finally:
        s.close()

def assign_report_permissions(s, user, report_id, current_level):
    report = s.query(Report).filter_by(id=report_id).first()
    if current_level not in ['Editor', 'Owner']:
        st.error("Only editors and owners can manage permissions.")
        return

    org_id = report.organization_id
    users = s.query(User).filter_by(organization_id=org_id).all()
    user_options = {u.full_name: u.id for u in users if u.id != report.owner_id}  # Exclude owner
    groups = s.query(Group).filter_by(organization_id=org_id).all()
    group_options = {g.name: g.id for g in groups}
    permission_colors = {
        "Viewer": "#e6ecfd",
        "Commenter": "#fff8db",
        "Editor": "#e8f9ee",
        "Owner": "#d1f9e2",
    }
    permission_icons = {
        "Viewer": "fa-eye",
        "Commenter": "fa-comments",
        "Editor": "fa-pen-to-square",
        "Owner": "fa-crown"
    }

    st.markdown("""
        <div style='margin-bottom:12px;padding:12px 16px;background:#f6f9fc;border-radius:11px;'><i class='fa-solid fa-user-lock'></i>
        <b>Manage Access</b>: Assign individual and group permissions for this report.
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        selected_users = st.multiselect("Select users", list(user_options.keys()))
        user_level = st.selectbox("Permission for users", ["Viewer", "Commenter", "Editor"])
    with col2:
        selected_groups = st.multiselect("Select groups", list(group_options.keys()))
        group_level = st.selectbox("Permission for groups", ["Viewer", "Commenter", "Editor"])

    if st.button("💾 Save Permissions"):
        s.query(ReportPermission).filter(
            ReportPermission.report_id == report_id,
            ReportPermission.level != 'Owner'
        ).delete()
        for name in selected_users:
            perm = ReportPermission(id=str(uuid.uuid4()), report_id=report_id, user_id=user_options[name], level=user_level)
            s.add(perm)
        for name in selected_groups:
            perm = ReportPermission(id=str(uuid.uuid4()), report_id=report_id, group_id=group_options[name], level=group_level)
            s.add(perm)
        s.commit()
        st.success("Permissions saved successfully! <i class='fa-solid fa-lock'></i>", unsafe_allow_html=True)

    st.markdown("### <i class='fa-solid fa-user-shield'></i> Current Permissions", unsafe_allow_html=True)
    perms = s.query(ReportPermission).filter_by(report_id=report_id).all()
    perm_data = []
    for p in perms:
        if p.user_id:
            user_name = s.query(User).filter_by(id=p.user_id).first().full_name
            icon = permission_icons.get(p.level, "fa-user")
            color = permission_colors.get(p.level, "#eaeaea")
            badge_html = f"<span style='background:{color};padding:2px 9px;border-radius:5px;font-size:.95em;margin-left:7px;'><i class='fa-solid {icon}'></i> {p.level}</span>"
            perm_data.append(f"<b><i class='fa-solid fa-user'></i> {user_name}</b> {badge_html}")
        elif p.group_id:
            group_name = s.query(Group).filter_by(id=p.group_id).first().name
            icon = permission_icons.get(p.level, "fa-users")
            color = permission_colors.get(p.level, "#eaeaea")
            badge_html = f"<span style='background:{color};padding:2px 9px;border-radius:5px;font-size:.95em;margin-left:7px;'><i class='fa-solid {icon}'></i> {p.level}</span>"
            perm_data.append(f"<b><i class='fa-solid fa-users'></i> {group_name}</b> {badge_html}")

    if perm_data:
        for row in perm_data:
            st.markdown(row, unsafe_allow_html=True)
    else:
        st.info("No permissions set.")


def save_file(df, filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        df.to_csv(filepath, index=False)
    elif ext == '.xlsx':
        df.to_excel(filepath, index=False)

def save_comment(s, report_id, user_id, comment):
    if not comment.strip():
        st.error("Comment cannot be empty.")
        return
    new_comment = Comment(
        id=str(uuid.uuid4()),
        report_id=report_id,
        user_id=user_id,
        comment=comment
    )
    s.add(new_comment)
    s.commit()


def display_comments(s, report_id):
    comments = s.query(Comment).filter_by(report_id=report_id).order_by(Comment.created_at.desc()).all()
    if comments:
        for c in comments:
            user = s.query(User).filter_by(id=c.user_id).first()
            st.write(f"**{user.full_name}** ({c.created_at.strftime('%Y-%m-%d %H:%M')}): {c.comment}")
    else:
        st.info("No comments yet.")

def delete_report(s, report_id):
    report = s.query(Report).filter_by(id=report_id).first()
    if report:
        if os.path.exists(report.filepath):
            os.remove(report.filepath)
        s.delete(report)
        s.commit()


def home_reports_list():
    st.subheader("Your Reports")
    user = st.session_state.user
    if user['role_name'] == 'Superadmin':
        st.info("Superadmins do not have personal reports.")
        return
    
    s = SessionLocal()
    try:
        # Fetch reports not in any folder for simplicity, or adapt to show all
        reports = fetch_reports(s, user, folder_id=None)
        if not reports:
            st.info("You have no reports yet.")
            return
        
        for r in reports:
            display_report_item(s, user, r)  # Reuse your existing display function

    except Exception as e:
        st.error(f"Error loading reports: {str(e)}")
    finally:
        s.close()
