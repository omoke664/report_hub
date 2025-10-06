# page/home_page.py
import streamlit as st
import pandas as pd
from db import get_session
from models import Organization, Report, Dashboard, User
import plotly.express as px
from modules.utils import safe_rerun  
import datetime 


st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
""", unsafe_allow_html=True)



def home_page():
    """Dynamic homepage based on role."""
    role = st.session_state.user.get("role_name")
    user_id = st.session_state.user.get("id")
    org_id = st.session_state.user.get("organization_id")

    st.title("Home")

    if role == "Superadmin":
        superadmin_home()
    elif role == "Admin":
        admin_home(user_id, org_id)
    else:
        user_home(user_id, org_id)


# -------------------------
# Superadmin Home
# -------------------------
def superadmin_home():
    st.markdown("""
        <style>
          .card {background: #fff; border-radius: 16px; box-shadow: 0 2px 20px rgba(0,0,0,0.04); padding: 21px 27px 17px 27px; margin-bottom: 14px;}
          .metric-icon {font-size: 2.2em; text-align:center; margin-bottom: 2px;}
          .metric-icon i {font-size: 1.3em; color: #1a1a2b;}
          .tag {display: inline-block; background: #15131c; color: #fff; font-size: .88em; padding: 2px 9px; border-radius: 7px; margin-left: 8px;}
        </style>
    """, unsafe_allow_html=True)

    st.subheader("System Overview")
    session = get_session()
    try:
        now = datetime.datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start = now - datetime.timedelta(days=now.weekday())

        org_count = session.query(Organization).count()
        orgs_this_month = session.query(Organization).filter(Organization.created_at >= month_start).count()

        user_count = session.query(User).count()
        users_this_month = session.query(User).filter(User.created_at >= month_start).count()

        report_count = session.query(Report).count()
        reports_this_week = session.query(Report).filter(Report.created_at >= week_start).count()

        dashboard_count = session.query(Dashboard).count()
        dashboards_this_week = session.query(Dashboard).filter(Dashboard.created_at >= week_start).count()

        # Use icons instead of emojis
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-building"></i></div>', unsafe_allow_html=True)
            st.metric("Total Organizations", org_count, f"+{orgs_this_month} this month")
        with col2:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-users"></i></div>', unsafe_allow_html=True)
            st.metric("Total Users", user_count, f"+{users_this_month} this month")
        with col3:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-file-lines"></i></div>', unsafe_allow_html=True)
            st.metric("Total Reports", report_count, f"+{reports_this_week} this week")
        with col4:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-chart-column"></i></div>', unsafe_allow_html=True)
            st.metric("Dashboards", dashboard_count, f"+{dashboards_this_week} this week")

        st.markdown("""
            <div class="card" style="display: flex; flex-wrap: wrap; gap: 24px; margin-top: 18px;">
              <div><i class="fa-solid fa-server"></i> <span class="tag" style="background:#e7faeb; color:#1ca36a;">API Server: Online</span></div>
              <div><i class="fa-solid fa-database"></i> <span class="tag" style="background:#e7f6fa; color:#1596b4;">Database: Healthy</span></div>
              <div><i class="fa-solid fa-folder"></i> <span class="tag" style="background:#fae7eb; color:#b41c30;">File Storage: Online</span></div>
              <div><i class="fa-solid fa-chart-line"></i> <span class="tag" style="background:#f6e7fa; color:#851cb4;">Analytics Engine: Running</span></div>
            </div>
        """, unsafe_allow_html=True)

        st.info("As Superadmin, you manage the entire system.")
        st.write("➡️ Use the sidebar to create and manage organizations.")

        # Recent Organizations cards with icon
        recent_orgs = session.query(Organization).order_by(Organization.created_at.desc()).limit(5).all()
        st.markdown("### Recent Organizations")
        if recent_orgs:
            for o in recent_orgs:
                st.markdown(f"""
                    <div class="card" style="margin-bottom:10px;">
                      <i class="fa-solid fa-building" style="color:#5a7dff"></i>
                      <b>{o.name}</b> <span class="tag" style="background:#15131c;">active</span><br>
                      <span style="font-size:.93em;">{len(o.users)} users · Created {o.created_at.strftime("%b %d, %Y")}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No organizations created yet.")

    finally:
        session.close()
# -------------------------
# Admin Home
# -------------------------
def admin_home(user_id, org_id):
    st.markdown("""
        <style>
          .card {background: #fff; border-radius: 16px; box-shadow: 0 2px 20px rgba(0,0,0,0.04); padding: 21px 27px 17px 27px; margin-bottom: 14px;}
          .metric-icon {font-size: 2.2em; text-align:center; margin-bottom: 2px;}
          .metric-icon i {font-size: 1.3em; color: #1a1a2b;}
          .tag {display: inline-block; background: #15131c; color: #fff; font-size: .88em; padding: 2px 9px; border-radius: 7px; margin-left: 8px;}
        </style>
    """, unsafe_allow_html=True)
    st.subheader("Organization Overview")
    session = get_session()
    try:
        now = datetime.datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start = now - datetime.timedelta(days=now.weekday())

        user_count = session.query(User).filter_by(organization_id=org_id).count()
        users_this_month = session.query(User).filter(
            User.organization_id == org_id,
            User.created_at >= month_start).count()

        report_count = session.query(Report).filter_by(organization_id=org_id).count()
        reports_this_week = session.query(Report).filter(
            Report.organization_id == org_id,
            Report.created_at >= week_start).count()

        dashboard_count = session.query(Dashboard).filter_by(organization_id=org_id).count()
        dashboards_this_week = session.query(Dashboard).filter(
            Dashboard.organization_id == org_id,
            Dashboard.created_at >= week_start).count()

        # Replace emojis with icons
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-users"></i></div>', unsafe_allow_html=True)
            st.metric("Team Members", user_count, f"+{users_this_month} this month")
        with col2:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-file-lines"></i></div>', unsafe_allow_html=True)
            st.metric("Reports", report_count, f"+{reports_this_week} this week")
        with col3:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-chart-column"></i></div>', unsafe_allow_html=True)
            st.metric("Dashboards", dashboard_count, f"+{dashboards_this_week} this week")

        st.info("As Admin, you can invite users, manage groups, and organize reports/dashboards.")
        st.write("➡️ Use the sidebar to manage your organization.")

        # Recent Reports (cards)
        recent_reports = session.query(Report).filter_by(organization_id=org_id).order_by(Report.created_at.desc()).limit(5).all()
        st.markdown("### Recent Reports")
        if recent_reports:
            for r in recent_reports:
                st.markdown(f"""
                  <div class="card" style="margin-bottom:8px;">
                    <i class="fa-solid fa-file-lines" style="color:#8278fa"></i>
                    <b>{r.title}</b> <span class="tag"><i class="fa-solid fa-circle-check"></i> published</span><br>
                    <span style="font-size:.93em;">by <b>{getattr(r.owner, 'full_name', 'N/A')}</b> · {r.created_at.strftime("%b %d, %Y")}</span>
                  </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No reports created yet.")

        # Recent Dashboards (cards + pie chart)
        recent_dashboards = session.query(Dashboard).filter_by(organization_id=org_id).order_by(Dashboard.created_at.desc()).limit(5).all()
        st.markdown("### Recent Dashboards")
        if recent_dashboards:
            for d in recent_dashboards:
                st.markdown(f"""
                  <div class="card" style="margin-bottom:8px;">
                    <i class="fa-solid fa-chart-column" style="color:#3ae374"></i>
                    <b>{d.name}</b> <span style="background:#e7faeb; color:#1ca36a; padding:2px 7px; border-radius:5px; font-size:.89em;"><i class="fa-solid fa-bolt"></i> active</span><br>
                    <span style="font-size:.93em;">{d.description or '<i>No description</i>'} · {d.created_at.strftime("%b %d, %Y")}</span>
                  </div>
                """, unsafe_allow_html=True)
            pie_df = pd.DataFrame({
                "Dashboard": [d.name for d in recent_dashboards],
                "Length of Description": [len(d.description or "") for d in recent_dashboards]
            })
            import plotly.express as px
            fig = px.pie(pie_df, names="Dashboard", values="Length of Description",
                         title="Dashboard Description Length Distribution")
            st.plotly_chart(fig)
        else:
            st.info("No dashboards created yet.")

    finally:
        session.close()

# -------------------------
# User Home
# -------------------------
def user_home(user_id, org_id):
    st.markdown("""
        <style>
          .card {background: #fff; border-radius: 16px; box-shadow: 0 2px 16px rgba(0,0,0,0.04); padding: 20px 24px 14px 24px; margin-bottom: 12px;}
          .metric-icon {font-size: 2em; text-align:center; margin-bottom: 5px;}
          .metric-icon i {font-size: 1.3em; color: #1931c2;}
          .badge {display: inline-block; background: #eee; color: #222; font-size: .88em; padding: 2px 9px; border-radius: 7px; margin-left: 7px;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="card" style="margin-bottom:20px;background:#f9f9fa;">'
        "<i class='fa-solid fa-house-user'></i> Welcome back! <br /><span style='font-size:.97em;color:#949494;'>Here\'s what\'s happening with your reports today.</span></div>",
        unsafe_allow_html=True
    )

    session = get_session()
    try:
        now = datetime.datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start = now - datetime.timedelta(days=now.weekday())

        my_reports = session.query(Report).filter_by(owner_id=user_id).order_by(Report.created_at.desc()).all()
        reports_this_month = session.query(Report).filter(
            Report.owner_id == user_id,
            Report.created_at >= month_start
        ).count()

        org_dashboards = session.query(Dashboard).filter_by(organization_id=org_id).order_by(Dashboard.created_at.desc()).all()
        dashboards_this_week = session.query(Dashboard).filter(
            Dashboard.organization_id == org_id,
            Dashboard.created_at >= week_start
        ).count()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-file-lines"></i></div>', unsafe_allow_html=True)
            st.metric("My Reports", len(my_reports), f"+{reports_this_month} this month")
        with col2:
            st.markdown('<div class="card metric-icon"><i class="fa-solid fa-chart-column"></i></div>', unsafe_allow_html=True)
            st.metric("Org Dashboards", len(org_dashboards), f"+{dashboards_this_week} this week")

        st.info("As a User, you can generate reports and view dashboards.")
        st.write("➡️ Use the sidebar for quick access to your reports and dashboards.")

        if my_reports:
            st.markdown("### My Recent Reports")
            for r in my_reports[:5]:
                st.markdown(
                    f"""
                    <div class="card" style="margin-bottom:8px;">
                        <i class="fa-solid fa-file-lines" style="color:#1931c2"></i>
                        <b>{r.title}</b> <span class="badge">{r.filename}</span><br>
                        <span style="font-size:.92em;">{r.created_at.strftime('%b %d, %Y')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            reports_df = pd.DataFrame(
                [{"Date": r.created_at.date(), "Report": r.title} for r in my_reports]
            )
            reports_count = reports_df.groupby("Date").count().reset_index()
            fig = px.line(
                reports_count,
                x="Date",
                y="Report",
                title="Reports Created Over Time",
                markers=True,
                hover_data={"Date": True, "Report": True},
            )
            st.plotly_chart(fig)
        else:
            st.info("You haven't created any reports yet.")

        if org_dashboards:
            st.markdown("### Recent Dashboards in Org")
            for d in org_dashboards[:5]:
                st.markdown(
                    f"""
                    <div class="card" style="margin-bottom:8px;">
                        <i class="fa-solid fa-chart-column" style="color:#21a179"></i>
                        <b>{d.name}</b> <span class="badge">{d.description or "No description"}</span><br>
                        <span style="font-size:.91em;">{d.created_at.strftime('%b %d, %Y')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            pie_df = pd.DataFrame(
                {
                    "Dashboard": [d.name for d in org_dashboards[:5]],
                    "Desc Length": [len(d.description or "") for d in org_dashboards[:5]],
                }
            )
            fig = px.pie(
                pie_df,
                names="Dashboard",
                values="Desc Length",
                title="Dashboard Description Length Distribution",
            )
            st.plotly_chart(fig)
        else:
            st.info("No dashboards available in your organization yet.")
    finally:
        session.close()