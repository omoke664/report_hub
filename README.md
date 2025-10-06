# 📊 Report Hub

**Report Hub** is a robust, scalable report management platform built with **Streamlit** and modular **Python** components.  
It enables teams to collect, organize, share, and visualize reports and dashboards — all with granular permissions and role controls.

---

## 🧭 Table of Contents

- [Overview](#-overview)
- [Project Goals](#-project-goals)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Directory & Folder Layout](#-directory--folder-layout)
- [Entity Relationships](#-entity-relationships)
- [Module Descriptions](#-module-descriptions)
  - [app.py](#apppy)
  - [db.py](#dbpy)
  - [models.py](#modelspy)
  - [Other Modules](#other-modules)
- [Database Schema](#-database-schema)
- [Backup & Recovery](#-backup--recovery)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Workflow](#workflow-overview)
  - [Uploading Reports](#uploading-reports)
  - [Managing Users, Orgs, and Groups](#managing-users-orgs-groups)
  - [Permission Controls](#permission-controls)
  - [Dashboard Creation & Sharing](#dashboard-creation--sharing)
  - [Commenting System](#commenting-system)
- [Contributing](#-contributing)
- [License](#-license)
- [FAQ](#-faq)

---

## 🏗 Overview

Report Hub centralizes organizational knowledge by providing a **secure**, **collaborative**, and **structured** dashboard/report management system.  
It’s designed for teams that need workflow structure, integrated data sources, controlled sharing, and collaborative analytics — all within an intuitive **Streamlit UI**.

---

## 🎯 Project Goals

- Centralize report access for organizations and teams  
- Enable secure sharing and permission management  
- Automate organization of reports into folders and dashboards  
- Support collaboration through commenting and reviews  
- Preserve data via integrated backup and recovery  
- Allow easy extensibility for new features or data sources  

---

## ⚙️ Features

- User, Organization, and Group management  
- Role assignment: **Admin**, **Owner**, **Member**, **Guest**  
- Secure report uploads and folder organization  
- Dashboard creation linking multiple reports  
- Role-based access control (view/edit/manage)  
- Real-time commenting on reports/dashboards  
- Backup/restore to CSV or SQLite  
- Alembic integration for schema migrations  
- Modular, maintainable code structure  
- Responsive web interface with **Streamlit**  

---

## 🧩 System Architecture

| Component | Description |
|------------|-------------|
| **Frontend** | Streamlit web interface (`/page`) |
| **Backend** | SQLAlchemy ORM + SQLite (can be replaced with other RDBMS) |
| **Modules** | Located in `/modules` for business logic and workflows |
| **Migrations** | Handled via Alembic in `/alembic` |
| **Storage** | User uploads stored in `/uploads` |
| **Backup** | Separate DB/CSV backups for reliability |

---

## 📁 Directory & Folder Layout

report_hub/
└── streamlit_report_hub/
└── report_manager_streamlit/
├── alembic/ # Database migrations and versions
├── modules/ # Helper and logic modules
├── page/ # UI page components
├── uploads/ # Uploaded report files
├── app.py # Main Streamlit app
├── db.py # Database session and init code
├── models.py # ORM models and relationships
├── report_manager.db # Main SQLite DB
├── report_manager_backup.db # Backup database
├── dashboards_backup.csv # Dashboard backup
└── README.md # Project documentation


---

## 🧠 Entity Relationships

- **User** – Belongs to Organizations and Groups; owns Reports/Dashboards  
- **Organization** – Contains Folders, Groups, Users, Dashboards, Reports  
- **Group** – Subset of Users for shared access control  
- **Report** – Uploaded file, linked to Folders and Dashboards  
- **Folder** – Logical container for Reports/Dashboards  
- **Dashboard** – Aggregates visualizations from related Reports  
- **Permission** – Defines user/group access levels (read/write/admin)  
- **Comment** – Enables collaboration on individual Reports/Dashboards  

---

## 🧮 Module Descriptions

### `app.py`
- Entry point for the Streamlit application  
- Handles routing, navigation, and session state management  

### `db.py`
- Manages database connections and transactions  
- Initializes tables defined in `models.py`

### `models.py`
- Defines ORM entities:
  - `User`, `Organization`, `Report`, `Folder`, `Dashboard`, `Group`, `Permission`, `Comment`
- Manages table relationships and cascades  

### Other Modules
- `modules/`: Core business logic (validation, reporting, logging)  
- `page/`: Streamlit page components (auth, dashboards, etc.)  
- `alembic/`: Migration scripts and version tracking  

---

## 🗃 Database Schema

- Default DB: **SQLite** (`report_manager.db`)  
- Entities defined in `models.py`  
- Migrations managed by Alembic  
- Backups exported as `.db` or `.csv` files  

---

## 💾 Backup & Recovery

- Backups stored as both **CSV** and **SQLite** copies  
- Restore by replacing `report_manager.db` or importing CSVs  
- Versioning handled through Alembic migration scripts in `/alembic`

---

## ⚡ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/omoke664/report_hub.git
cd report_hub/streamlit_report_hub/report_manager_streamlit


2. Install Dependencies
pip install -r requirements.txt


If missing, create a requirements.txt including:

streamlit
sqlalchemy
alembic
pandas

3. Run the Application
streamlit run app.py

⚙️ Configuration

Database: Default SQLite (report_manager.db), configurable in db.py

Backup Folder: Set in app.py

Migrations: Run schema upgrades via:

alembic upgrade head


Generate migration scripts:

alembic revision --autogenerate -m "Your migration message"
alembic upgrade head

🚀 Usage
Workflow Overview

Login or register a user

Upload reports

Create folders and dashboards

Assign permissions and share dashboards

Collaborate using comments

Backup or export data when needed

Uploading Reports

Upload files via the UI

Assign reports to folders and dashboards

Files saved in /uploads with DB metadata

Managing Users, Orgs, Groups

Admins create Organizations and Groups

Assign users to groups and roles (Admin/Owner/Member/Guest)

Permission Controls

Fine-grained control at user/group level

Permissions include read, write, admin

Ensures secure report and dashboard sharing

Dashboard Creation & Sharing

Combine multiple reports into dashboards

Share dashboards with users/groups

Optionally export dashboards as PDF

Commenting System

Add comments to dashboards and reports

Supports real-time team collaboration

🤝 Contributing

Fork the repository

Create a feature branch

Implement and test changes

Submit a pull request with a clear description
