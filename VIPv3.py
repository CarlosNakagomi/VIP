# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from base64 import b64encode
import mimetypes
import random

# -------------------------------------------------------------
# VIP – Landing + Auth + Dashboard(Unificado: Dashboard + Admin)
# -------------------------------------------------------------

st.set_page_config(
    page_title="VIP • Venue Intelligence Platform",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================
#   SESSION DEFAULTS
# =====================
if "route" not in st.session_state:
    st.session_state.route = "landing"
if "users" not in st.session_state:
    st.session_state.users = {}
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# navegação unificada (dashboard + admin)
DASH_SECTIONS = [
    ("🔎 Search & Filter Marketplace", "dash_market"),
    ("🗂️ RFP Submission History", "dash_rfp_hist"),
    ("💳 Transaction History", "dash_tx"),
    ("🔔 Notification Center", "dash_notifs"),
    ("💬 Chat / Messaging Center", "dash_chat"),
]
ADMIN_SECTIONS = [
    ("👥 Users", "admin_users"),
    ("📈 Analytics", "admin_analytics"),
    ("🚩 Disputes", "admin_disputes"),
    ("📣 Communications", "admin_comm"),
    ("🚀 Promo/Boost", "admin_promo"),
    ("📦 Data Clients", "admin_clients"),
    ("📊 Site Charts", "admin_site"),
]
if "main_section" not in st.session_state:
    st.session_state.main_section = DASH_SECTIONS[0][1]  # default: marketplace

# =====================
#   SEEDS
# =====================
def _seed_notifications():
    return [
        {"id": 1, "title": "Payment confirmed",     "body": "Catering - $500 received.",       "ts": "2025-09-19 16:05", "ntype": "success", "read": True},
        {"id": 2, "title": "RFP response received", "body": "Vertex 161 sent a proposal.",     "ts": "2025-09-22 10:12", "ntype": "info",    "read": False},
        {"id": 3, "title": "New message",           "body": "Venue Harbor replied in chat.",   "ts": "2025-09-18 09:21", "ntype": "message", "read": False},
    ]
def _seed_transactions():
    return pd.DataFrame(
        [
            ["2025-09-10", "Harbor 412",  "Venue Booking",     300, "Completed", "TXN-001"],
            ["2025-09-12", "Helix 238",   "AV Support",        150, "Completed", "TXN-002"],
            ["2025-09-15", "Radiant 179", "Catering Deposit",  500, "Pending",   "TXN-003"],
            ["2025-09-18", "Vertex 161",  "Photography",       150, "Refunded",  "TXN-004"],
            ["2025-09-20", "Harbor 412",  "Venue Balance",     450, "Completed", "TXN-005"],
            ["2025-09-22", "Helix 238",   "Lighting",          220, "Completed", "TXN-006"],
        ],
        columns=["date", "counterparty", "service", "amount", "status", "ref"],
    )
def _seed_mail():
    return {
        "Inbox": [
            {"id": 101, "title": "Quote for AV package", "from": "Helix 238", "preview": "We can offer...", "msgs": [
                {"by":"Helix 238","ts":"2025-09-21 10:02","text":"We can offer AV package for $150."},
                {"by":"You","ts":"2025-09-21 10:10","text":"Thanks! Can you include microphones?"}
            ]},
            {"id": 102, "title": "Venue Harbor availability", "from": "Harbor 412", "preview": "Available on 10/15", "msgs":[
                {"by":"Harbor 412","ts":"2025-09-20 14:01","text":"We are available on 10/15."}
            ]},
        ],
        "Sent": [
            {"id": 201, "title": "Follow-up: Photography", "from": "Vertex 161", "preview": "Sharing brief...", "msgs":[
                {"by":"You","ts":"2025-09-18 16:00","text":"Sharing brief for photography needs."}
            ]},
        ],
        "Archived": []
    }

if "notifications" not in st.session_state:
    st.session_state.notifications = _seed_notifications()
if "transactions" not in st.session_state:
    st.session_state.transactions = _seed_transactions()
if "rfp_history" not in st.session_state:
    st.session_state.rfp_history = []
if "mail" not in st.session_state:
    st.session_state.mail = _seed_mail()
if "mail_folder" not in st.session_state:
    st.session_state.mail_folder = "Inbox"
if "mail_thread" not in st.session_state:
    st.session_state.mail_thread = st.session_state.mail["Inbox"][0]["id"] if st.session_state.mail["Inbox"] else None

# =====================
# CONSTANTS / PATHS
# =====================
ROLE_OPTIONS = ["For-Profit (Client)", "Non-Profit", "Venue", "Vendor"]
ADMIN_ROLE = "Admin"

ROOT = Path(__file__).resolve().parent
LOGO_PATH = ROOT / "assets" / "logo.png"
DATA_PATH = ROOT / "data" / "marketplace_clean_numeric.csv"

# =====================
# STYLES
# =====================
st.markdown(
    """
    <style>
      .vip-wrap{padding:0 8px 40px;}
      .vip-hero{display:flex;flex-direction:column;align-items:center;gap:10px;margin:20px auto;}
      .vip-badge{display:inline-block;padding:6px 10px;border-radius:9999px;background:#0ea5e9;color:white;font-size:12px;}
      .vip-title{font-size:34px;font-weight:800;color:#111827;}
      .vip-sub{font-size:15px;color:#374151;margin-bottom:8px;}
      .vip-ctas{display:flex;gap:12px;justify-content:center;width:100%;max-width:720px;margin:12px 0;}
      .vip-footer{color:#6b7280;text-align:center;margin-top:18px;}
      .muted{color:#6b7280;font-size:12px;}
      .kpi{background:#ecfdf5;border:1px solid #d1fae5;border-radius:14px;padding:16px;box-shadow:0 6px 14px rgba(0,0,0,.08);}
      .kpi h4{margin:0;color:#065f46;font-weight:700;font-size:13px}
      .kpi .v{margin-top:6px;color:#047857;font-weight:800;font-size:26px}
      .vip-card{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;box-shadow:0 6px 14px rgba(0,0,0,.06);}
      .bubble-u { background:#e5f0ff; padding:8px 10px; border-radius:10px; margin:6px 0; display:inline-block; }
      .bubble-a { background:#dcfce7; padding:8px 10px; border-radius:10px; margin:6px 0; display:inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================
# HELPERS
# =====================
def render_centered_image(path: str, max_width_px: int = 900):
    p = Path(path)
    if p.exists():
        data = p.read_bytes()
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        b64 = b64encode(data).decode()
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:18px 0;">
              <img src="data:{mime};base64,{b64}" style="max-width:{max_width_px}px;width:100%;height:auto;border-radius:6px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:18px 0;">
              <img src="https://via.placeholder.com/1200x480?text=Venue+Intelligence+Platform"
                   style="max-width:900px;width:100%;height:auto;border-radius:6px;" />
            </div>
            """, unsafe_allow_html=True
        )

def nav(route: str):
    st.session_state["route"] = route
    st.rerun()

def request_nav(route: str):
    st.session_state["route"] = route
    st.session_state["_pending_nav"] = True

def create_user(username, password, role, full_name="", contact=""):
    key = (username or "").strip().lower()
    if not key:
        return False, "Username is required."
    if key in st.session_state.users:
        return False, "An account with this username already exists."
    st.session_state.users[key] = {
        "password": password or "",
        "full_name": (full_name or "").strip(),
        "contact": (contact or "").strip(),
        "role": role,
        "status": "Active",
    }
    return True, "Account created successfully."

def authenticate(username, password):
    key = (username or "").strip().lower()
    user = st.session_state.users.get(key)
    if not user:
        return False, "No account found with this username."
    if user["password"] != (password or ""):
        return False, "Incorrect password."
    st.session_state.current_user = {"username": key, **user}
    return True, "Login successful."

def logout():
    st.session_state.current_user = None
    nav("landing")

def unread_count() -> int:
    return sum(1 for n in st.session_state.notifications if not n.get("read", False))

# =====================
#  MARKETPLACE
# =====================
def _safe_read_marketplace(path: str):
    try:
        df = pd.read_csv(path)
        return df, None
    except Exception as e:
        return None, str(e)

def render_marketplace():
    st.subheader("🔎 Search & Filter Marketplace")
    df, err = _safe_read_marketplace(DATA_PATH)
    if err or df is None:
        st.error(f"Could not load marketplace data: {err or 'Unknown error'}")
        return

    if "rating" in df.columns:
        df["rating"] = df["rating"].round(1)

    c1, c2, c3 = st.columns(3)
    with c1:
        type_filter = st.selectbox("Type", ["All"] + sorted(df["type"].dropna().unique().tolist()) if "type" in df.columns else ["All"])
    with c2:
        city_filter = st.selectbox("City", ["All"] + sorted(df["city"].dropna().unique().tolist()) if "city" in df.columns else ["All"])
    with c3:
        category_filter = st.selectbox("Category", ["All"] + sorted(df["category"].dropna().unique().tolist()) if "category" in df.columns else ["All"])

    if "price" in df.columns and pd.api.types.is_numeric_dtype(df["price"]):
        price_min, price_max = int(df["price"].min()), int(df["price"].max())
        sel_price = st.slider("Price range (USD)", price_min, price_max, (price_min, price_max), step=10)
    else:
        sel_price = (0, 10**9)

    q = st.text_input("Search by name or category")

    results = df.copy()
    if "type" in results.columns and type_filter != "All":
        results = results[results["type"] == type_filter]
    if "city" in results.columns and city_filter != "All":
        results = results[results["city"] == city_filter]
    if "category" in results.columns and category_filter != "All":
        results = results[results["category"] == category_filter]
    if "price" in results.columns and pd.api.types.is_numeric_dtype(results["price"]):
        results = results[(results["price"] >= sel_price[0]) & (results["price"] <= sel_price[1])]

    if q:
        ql = q.lower()
        name_mask = results["name"].astype(str).str.lower().str.contains(ql, na=False) if "name" in results.columns else False
        cat_mask = results["category"].astype(str).str.lower().str.contains(ql, na=False) if "category" in results.columns else False
        results = results[name_mask | cat_mask]

    display_cols = [c for c in ["name","category","city","capacity","price","rating","contact_email","type"] if c in results.columns]
    df_display = results[display_cols].copy()
    if "rating" in df_display.columns:
        df_display["rating"] = df_display["rating"].astype(str) + " ⭐"
    st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    selected_name = st.selectbox("Select an entry for RFP:", ["None"] + (df_display["name"].tolist() if "name" in df_display.columns else []))
    if selected_name != "None":
        item = results[results["name"] == selected_name].iloc[0].to_dict()
        st.success(f"Selected: {item['name']} ({item.get('type','—')}) in {item.get('city','—')} • ${item.get('price','—')}")
        if st.button("📝 Submit RFP for this selection"):
            st.session_state["selected_item"] = item
            nav("rfp")

# =====================
#  RFP WIZARD
# =====================
def _reset_rfp_state():
    for k in ["selected_item", "rfp_prefilled"]:
        st.session_state.pop(k, None)
    st.session_state["rfp_form_version"] = st.session_state.get("rfp_form_version", 0) + 1

def render_rfp(with_topbar: bool = True):
    st.header("📝 RFP Submission Wizard")
    item = st.session_state.get("selected_item")
    if item:
        st.info(
            f"Submitting RFP for **{item['name']}** "
            f"({item.get('type','—')}, {item.get('category','—')}) in **{item.get('city','—')}** — "
            f"Capacity: {item.get('capacity','—')} • Price: ${item.get('price','—')} • Contact: {item.get('contact_email','—')}"
        )

    v = st.session_state.get("rfp_form_version", 0)
    if "rfp_prefilled" not in st.session_state and item:
        default_title = f"Proposal for {item['name']}"
        st.session_state.rfp_prefilled = True
    else:
        default_title = ""

    with st.form(f"rfp_form_{v}", clear_on_submit=True):
        title     = st.text_input("Project Title", value=default_title, key=f"title_{v}")
        scope_txt = st.text_area("Scope / Requirements", value="", key=f"scope_{v}")
        date_in   = st.date_input("Target Date", key=f"date_{v}")
        budget    = st.text_input("Budget (USD)", value="", key=f"budget_{v}")
        files     = st.file_uploader("Attach Brief / Specs", accept_multiple_files=True, key=f"files_{v}")
        submitted = st.form_submit_button("Submit RFP")

    if submitted:
        st.session_state.rfp_history.insert(0, {
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": title or "(untitled)",
            "scope": scope_txt or "",
            "target_date": str(date_in) if isinstance(date_in, (date,)) else str(date_in),
            "budget": budget or "",
            "target_name": item['name'] if item else "",
            "target_type": item.get('type', '') if item else "",
            "target_city": item.get('city', '') if item else "",
            "target_contact": item.get('contact_email', '') if item else "",
            "price": item.get('price', '') if item else "",
        })

        # cria notificação + reexibe badge
        new_id = max([n["id"] for n in st.session_state.notifications] + [0]) + 1
        st.session_state.notifications.insert(0, {
            "id": new_id, "title": "RFP submitted",
            "body": f"Your RFP to {item['name'] if item else 'vendor'} was submitted.",
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ntype": "info", "read": False,
        })
        st.session_state.notif_badge_cleared = False

        st.success("✅ RFP submitted successfully!")
        if item:
            st.write(f"**Target:** {item['name']} ({item.get('type','—')}) — {item.get('contact_email','—')}")

        st.session_state.pop("selected_item", None)
        st.session_state.pop("rfp_prefilled", None)
        st.session_state["rfp_form_version"] = v + 1
        st.rerun()

    st.divider()
    if st.button("⬅️ Back to Marketplace"):
        _reset_rfp_state()
        nav("dashboard")

# =====================
#  TRANSACTIONS
# =====================
def render_transactions():
    st.subheader("💳 Transaction History")
    df = st.session_state.transactions.copy()

    c1, c2, c3 = st.columns(3)
    with c1:
        status = st.selectbox("Status", ["All"] + df["status"].unique().tolist())
    with c2:
        min_amt, max_amt = int(df["amount"].min()), int(df["amount"].max())
        amt = st.slider("Amount range", min_amt, max_amt, (min_amt, max_amt), step=10)
    with c3:
        q = st.text_input("Search (counterparty / service / ref)")

    if status != "All":
        df = df[df["status"] == status]
    df = df[(df["amount"] >= amt[0]) & (df["amount"] <= amt[1])]
    if q:
        ql = q.lower()
        df = df[df.apply(lambda r: ql in str(r["counterparty"]).lower() or
                                   ql in str(r["service"]).lower() or
                                   ql in str(r["ref"]).lower(), axis=1)]
    st.dataframe(df.reset_index(drop=True), use_container_width=True)

# =====================
#  NOTIFICATIONS (center)
# =====================
def render_notifications_center():
    st.subheader("🔔 Notification Center")
    notifs = sorted(st.session_state.notifications, key=lambda n: n.get("ts",""), reverse=True)
    if not notifs:
        st.info("No notifications yet.")
        return
    for n in notifs:
        with st.container(border=True):
            st.markdown(f"**{n.get('title','(no title)')}**  \n{n.get('body','')}  \n"
                        f"<span class='muted'>{n.get('ts','')}</span>", unsafe_allow_html=True)

# =====================
#  MESSAGING
# =====================
def render_messaging_center():
    st.subheader("💬 Chat / Messaging Center")
    col_left, col_mid, col_right = st.columns([1.1, 1.6, 2.2], gap="large")

    with col_left:
        st.markdown("**Folders**")
        for f in ["Inbox","Sent","Archived"]:
            if st.button(("📥 " if f=="Inbox" else "📤 " if f=="Sent" else "🗂️ ") + f, key=f"folder-{f}", use_container_width=True):
                st.session_state.mail_folder = f
                threads = st.session_state.mail[f]
                st.session_state.mail_thread = threads[0]["id"] if threads else None
                st.rerun()

    with col_mid:
        st.markdown(f"**{st.session_state.mail_folder}**")
        threads = st.session_state.mail[st.session_state.mail_folder]
        if not threads:
            st.info("No threads.")
        else:
            for th in threads:
                btn = st.button(f"{th['title']} — {th['from']}\n{th['preview']}", key=f"thread-{th['id']}", use_container_width=True)
                if btn:
                    st.session_state.mail_thread = th["id"]
                    st.rerun()

    with col_right:
        thobj = None
        for th in threads:
            if th["id"] == st.session_state.mail_thread:
                thobj = th
                break
        if not thobj:
            st.info("Select a thread to view the conversation.")
        else:
            st.markdown(f"**{thobj['title']}**  \n<span class='muted'>From: {thobj['from']}</span>", unsafe_allow_html=True)
            with st.container(border=True, height=360):
                for m in thobj["msgs"]:
                    if m["by"] == "You":
                        st.markdown(f"<div class='bubble-u'><b>You:</b> {m['text']}<br><span class='muted'>{m['ts']}</span></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='bubble-a'><b>{m['by']}:</b> {m['text']}<br><span class='muted'>{m['ts']}</span></div>", unsafe_allow_html=True)

            new_msg = st.text_input("Type a message", key=f"msg-input-{st.session_state.mail_thread}")
            if st.button("Send", key=f"send-{st.session_state.mail_thread}"):
                thobj["msgs"].append({"by":"You","ts":datetime.now().strftime("%Y-%m-%d %H:%M"),"text":new_msg or "(empty)"})
                st.success("Message sent.")
                st.rerun()

# =====================
#  ADMIN HELPERS / DATA
# =====================
def _seed_admin_disputes():
    return [
        {"id": 9001, "created":"2025-09-22 11:10", "type":"Payment", "from":"Helix 238",
         "against":"Harbor 412", "summary":"Refund disagreement (TXN-004)", "status":"Open"},
        {"id": 9002, "created":"2025-09-23 09:45", "type":"Content", "from":"Vertex 161",
         "against":"Radiant 179", "summary":"Misleading portfolio images", "status":"Under review"},
    ]
def _seed_broadcast_log():
    return [
        {"sent_at":"2025-09-21 17:05", "segment":"All Vendors", "subject":"Platform maintenance",
         "body":"Short notice: maintenance 02:00–03:00 UTC.", "via":"Email"}
    ]
def _seed_promo_campaigns():
    return [
        {"id":7001, "name":"October Spotlight", "segment":"Venues", "budget":200, "status":"Active"},
        {"id":7002, "name":"Boost – Photography", "segment":"Vendors (Photography)", "budget":150, "status":"Paused"},
    ]
if "admin_disputes" not in st.session_state:
    st.session_state.admin_disputes = _seed_admin_disputes()
if "broadcast_log" not in st.session_state:
    st.session_state.broadcast_log = _seed_broadcast_log()
if "promo_campaigns" not in st.session_state:
    st.session_state.promo_campaigns = _seed_promo_campaigns()
if "data_clients" not in st.session_state:
    st.session_state.data_clients = [
        {"id":3001, "name":"Acme Insights", "plan":"Pro (Monthly)", "status":"Active"},
        {"id":3002, "name":"CivicData", "plan":"Basic (Annual)", "status":"Trial"},
    ]

# Seed Admin user (usuario: admin, senha: admin)
if "users" in st.session_state and "admin" not in st.session_state.users:
    st.session_state.users["admin"] = {
        "password": "admin", "full_name":"Platform Admin",
        "contact":"admin@vip.local", "role": ADMIN_ROLE, "status": "Active"
    }

TAB_DESC = {
    # dashboard
    "dash_market": "Browse and filter venues/vendors.",
    "dash_rfp_hist": "Your submitted RFPs.",
    "dash_tx": "Payments and order history.",
    "dash_notifs": "All platform notifications.",
    "dash_chat": "Threaded messages with venues/vendors.",
    # admin
    "admin_users": "Manage accounts, roles and status.",
    "admin_analytics": "KPIs, trends and tables.",
    "admin_disputes": "Flagged content & payment issues.",
    "admin_comm": "Broadcast email/SMS to segments.",
    "admin_promo": "Create and manage boost campaigns.",
    "admin_clients": "Export anonymized datasets to B2B.",
    "admin_site": "Marketing-style demo charts.",
}

# renderizadores das seções admin
def admin_render_users():
    st.subheader("User Management")
    df = pd.DataFrame([
        {"username": u, "role": info.get("role"), "full_name": info.get("full_name",""),
         "contact": info.get("contact",""), "status": info.get("status","Active")}
        for u, info in st.session_state.users.items()
    ])
    st.dataframe(df, use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**Approve / Suspend**")
        target_user = st.selectbox("User", df["username"].tolist() if not df.empty else ["—"])
        new_status = st.selectbox("Set status", ["Active","Suspended"])
        if st.button("Apply status"):
            if target_user in st.session_state.users:
                st.session_state.users[target_user]["status"] = new_status
                st.success(f"{target_user} → {new_status}")
                st.rerun()
    with c2:
        st.markdown("**Change role**")
        role_user = st.selectbox("User ", df["username"].tolist() if not df.empty else ["—"], key="role_user")
        new_role = st.selectbox("Role", ROLE_OPTIONS + [ADMIN_ROLE], index=0)
        if st.button("Apply role"):
            if role_user in st.session_state.users:
                st.session_state.users[role_user]["role"] = new_role
                st.success(f"{role_user} → role {new_role}")
                st.rerun()
    with c3:
        st.markdown("**Reset password**")
        pw_user = st.selectbox("User  ", df["username"].tolist() if not df.empty else ["—"], key="pw_user")
        new_pw = st.text_input("New password", type="password")
        if st.button("Reset"):
            if pw_user in st.session_state.users:
                st.session_state.users[pw_user]["password"] = new_pw or ""
                st.success(f"Password reset for {pw_user}")
    with c4:
        st.markdown("**Create user (quick)**")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        r = st.selectbox("Role  ", ROLE_OPTIONS + [ADMIN_ROLE], key="new_role_sel")
        if st.button("Create user"):
            ok, msg = create_user(u, p, r, full_name=u, contact=f"{u}@example.com")
            st.success(msg) if ok else st.error(msg)
            if ok: st.rerun()

def admin_render_analytics():
    st.subheader("Analytics & Reporting Hub")
    tx = st.session_state.transactions.copy()
    rfps = pd.DataFrame(st.session_state.rfp_history) if st.session_state.get("rfp_history") else pd.DataFrame(columns=["submitted_at"])
    total_rev = int(tx.loc[tx["status"]=="Completed","amount"].sum()) if not tx.empty else 0
    pending = int(tx.loc[tx["status"]=="Pending","amount"].sum()) if not tx.empty else 0
    completed = int((tx["status"]=="Completed").sum()) if not tx.empty else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"<div class='kpi'><h4>Revenue (Completed)</h4><div class='v'>${total_rev:,.0f}</div></div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='kpi'><h4>Pending Payments</h4><div class='v'>${pending:,.0f}</div></div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='kpi'><h4>Completed Orders</h4><div class='v'>{completed}</div></div>", unsafe_allow_html=True)
    with k4:
        mrr = total_rev // 3 if total_rev else 0
        st.markdown(f"<div class='kpi'><h4>MRR (est.)</h4><div class='v'>${mrr:,.0f}</div></div>", unsafe_allow_html=True)

    cA, cB = st.columns(2)
    with cA:
        st.markdown("##### Revenue Trend (Demo)")
        df_line = _demo_series(days=20, base=120, volatility=18)
        st.line_chart(df_line.set_index("date"))
    with cB:
        st.markdown("##### Transactions by Status")
        if tx.empty:
            st.info("No transactions.")
        else:
            by_status = tx.groupby("status", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
            st.bar_chart(by_status.set_index("status"))

    st.markdown("<div class='vip-card'>", unsafe_allow_html=True)
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Transactions (latest)**")
        st.dataframe(tx.sort_values("date", ascending=False).head(25), use_container_width=True, height=260)
    with colB:
        st.markdown("**RFPs (last 30)**")
        st.dataframe(rfps.sort_values("submitted_at", ascending=False).head(30), use_container_width=True, height=260)
    st.markdown("</div>", unsafe_allow_html=True)

def admin_render_disputes():
    st.subheader("Flagged Content / Disputes")
    disp = st.session_state.admin_disputes
    if not disp:
        st.info("No disputes.")
        return
    for row in disp:
        with st.container(border=True):
            c1, c2 = st.columns([6,2])
            c1.markdown(f"**#{row['id']}** • {row['type']} • {row['summary']}  \n"
                        f"From: {row['from']}  →  Against: {row['against']}  \n"
                        f"<span class='muted'>{row['created']}</span>", unsafe_allow_html=True)
            new = c2.selectbox("Status", ["Open","Under review","Resolved","Rejected"],
                               index=["Open","Under review","Resolved","Rejected"].index(row["status"]),
                               key=f"disp-{row['id']}")
            if new != row["status"]:
                row["status"] = new

def admin_render_comm():
    st.subheader("Platform-Wide Communications (email/SMS)")
    seg = st.selectbox("Segment", ["All Users","All Vendors","All Venues","All NPOs/Clients"])
    subject = st.text_input("Subject")
    body = st.text_area("Message")
    via = st.selectbox("Channel", ["Email","SMS","Both"])
    if st.button("Send broadcast"):
        st.session_state.broadcast_log.insert(0, {
            "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "segment": seg, "subject": subject, "body": body, "via": via
        })
        st.success("Broadcast queued (demo).")
    st.markdown("**History**")
    st.dataframe(pd.DataFrame(st.session_state.broadcast_log), use_container_width=True, height=240)

def admin_render_promo():
    st.subheader("Promo / Boost Campaign Manager")
    dfc = pd.DataFrame(st.session_state.promo_campaigns)
    st.dataframe(dfc, use_container_width=True)
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        name = st.text_input("Campaign name")
    with c2:
        seg = st.text_input("Segment (label)")
    with c3:
        budget = st.number_input("Budget", min_value=0, value=100)
    st.write("")
    if st.button("Create campaign"):
        new_id = max([c["id"] for c in st.session_state.promo_campaigns]+[7000]) + 1
        st.session_state.promo_campaigns.append({"id":new_id,"name":name or f"Campaign {new_id}",
                                                 "segment":seg or "General","budget":int(budget),"status":"Active"})
        st.success("Campaign created.")
        st.rerun()

def admin_render_clients():
    st.subheader("Data Resale & Dashboard Clients (B2B)")
    dc = pd.DataFrame(st.session_state.data_clients)
    st.dataframe(dc, use_container_width=True)
    st.markdown("**Export anonymized datasets**")
    col1, col2 = st.columns(2)
    with col1:
        tx = st.session_state.transactions.copy()
        st.download_button("Download transactions.csv",
                           data=tx.to_csv(index=False).encode("utf-8"),
                           file_name="transactions.csv", mime="text/csv")
    with col2:
        rfps = pd.DataFrame(st.session_state.rfp_history) if st.session_state.get("rfp_history") else pd.DataFrame()
        st.download_button("Download rfp_history.csv",
                           data=rfps.to_csv(index=False).encode("utf-8"),
                           file_name="rfp_history.csv", mime="text/csv")

def admin_render_site():
    st.subheader("Demo Charts (marketing style)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Traffic Trend**")
        st.line_chart(_demo_series(days=30, base=200, volatility=25).set_index("date"))
    with c2:
        st.markdown("**Signups / Conversions**")
        df = pd.DataFrame({"metric":["Signups","Verified","Paying"],"value":[420,310,120]}).set_index("metric")
        st.bar_chart(df)
    st.markdown("**Category Performance**")
    df2 = pd.DataFrame({"Venue":[60,72,68,80,75],"Vendors":[40,55,62,70,66]}, index=[f"W{i}" for i in range(1,6)])
    st.area_chart(df2)

# util de série demo
def _demo_series(days=14, base=100, volatility=15):
    now = datetime.now()
    data, val = [], base
    for i in range(days):
        val = max(0, val + random.randint(-volatility, volatility))
        data.append({"date": (now - timedelta(days=days-i)).strftime("%Y-%m-%d"), "value": val})
    return pd.DataFrame(data)

# =====================
#  NAV BUTTONS (unificados)
# =====================
def render_unified_nav(is_admin: bool):
    """Linha 1: Dashboard | Linha 2: Admin (se admin)."""
    st.markdown("#### App Sections")

    # linha dashboard
    cols = st.columns(len(DASH_SECTIONS))
    for i, (label, key) in enumerate(DASH_SECTIONS):
        active = (st.session_state.main_section == key)
        if cols[i].button(label, use_container_width=True, key=f"nav-{key}"):
            st.session_state.main_section = key
            st.rerun()
        if active:
            cols[i].caption("active")

    # linha admin (só para admin)
    if is_admin:
        st.write("")
        cols2 = st.columns(len(ADMIN_SECTIONS))
        for i, (label, key) in enumerate(ADMIN_SECTIONS):
            active = (st.session_state.main_section == key)
            if cols2[i].button(label, use_container_width=True, key=f"nav-{key}"):
                st.session_state.main_section = key
                st.rerun()
            if active:
                cols2[i].caption("active")
    st.divider()

# =====================
#        ROUTES
# =====================
if st.session_state.route == "landing":
    st.markdown("<div class='vip-wrap'><section class='vip-hero'>", unsafe_allow_html=True)
    st.markdown("<span class='vip-badge'>🤝 FreeFuse × Sophist</span>", unsafe_allow_html=True)
    st.markdown("<div class='vip-title'>Venue Intelligence Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='vip-sub'>The operating system for nonprofit events — plan, book, and measure impact.</div>", unsafe_allow_html=True)
    render_centered_image(LOGO_PATH)
    st.markdown("<div class='vip-ctas'>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🆕 Sign Up", use_container_width=True):
            nav("signup")
    with c2:
        if st.button("🔐 Login", use_container_width=True):
            nav("login")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='vip-footer'>@2025 VIP • Privacy • Terms • Support</div>", unsafe_allow_html=True)
    st.markdown("</section></div>", unsafe_allow_html=True)

elif st.session_state.route == "signup":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    st.header("Create your account")
    with st.form("signup_form"):
        role = st.radio("Select your profile type", ROLE_OPTIONS, horizontal=True)  # sem Admin aqui
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name")
        contact = st.text_input("Contact (email or phone)")
        agree = st.checkbox("I agree to the Terms and Privacy Policy")
        submitted = st.form_submit_button("Create account")
        if submitted:
            if not (username and password and full_name and contact and agree):
                st.error("Please fill in all fields and accept the terms.")
            else:
                ok, msg = create_user(username, password, role, full_name, contact)
                if ok:
                    st.success(f"{msg} • Username: **{username}** • Role: **{role}**")
                    request_nav("login")
                else:
                    st.error(msg)
    if st.button("← Back"):
        nav("landing")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.route == "login":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    st.header("Welcome back")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_ok = st.form_submit_button("Login")
        if login_ok:
            ok, msg = authenticate(username, password)
            if ok:
                st.success(msg)
                request_nav("dashboard")
            else:
                st.error(msg)
    if st.button("← Back"):
        nav("landing")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.route == "dashboard":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    user = st.session_state.current_user
    if not user:
        st.warning("You are not logged in.")
        if st.button("Go to Login"):
            nav("login")
    else:
        # ======= TOP BAR: conta + único sino (só zera) =======
        with st.sidebar:
            st.markdown("### Account")
            st.write(f"**User:** {user['username']}")
            st.write(f"**Role:** {user['role']}")
            st.write(f"**Name:** {user.get('full_name', '—')}")
            st.write(f"**Contact:** {user.get('contact', '—')}")
            st.divider()
            if st.button("🔄 Switch Profile / Login"):
                nav("login")
            if st.button("🚪 Log out"):
                logout()

        top_l, top_r = st.columns([8,4])
        with top_l:
            st.markdown("### Dashboard")
            st.caption(f"Profile: **{user['role']}**")
        with top_r:
            c1, = st.columns(1)
            unread = unread_count()
            show_badge = (unread > 0) and (not st.session_state.get("notif_badge_cleared", False))
            notif_label = f"🔔 Notifications ({unread})" if show_badge else "🔔 Notifications"
            if c1.button(notif_label, use_container_width=True):
                for n in st.session_state.notifications:
                    n["read"] = True
                st.session_state.notif_badge_cleared = True
                st.rerun()

        # ======= NAV UNIFICADA =======
        is_admin = (user.get("role") == ADMIN_ROLE)
        render_unified_nav(is_admin)

        # ======= DESCRIÇÃO CURTA =======
        st.caption(TAB_DESC.get(st.session_state.main_section, ""))

        # ======= RENDER DA SEÇÃO ATIVA =======
        key = st.session_state.main_section
        # dashboard
        if key == "dash_market":            render_marketplace()
        elif key == "dash_rfp_hist":        # histórico de RFP
            st.subheader("🗂️ RFP Submission History")
            rows = st.session_state.get("rfp_history", [])
            if not rows:
                st.info("No RFP submissions yet.")
            else:
                df = pd.DataFrame(rows).sort_values("submitted_at", ascending=False)
                cols = ["submitted_at","title","target_name","target_type","target_city","budget","target_date","price","target_contact"]
                cols = [c for c in cols if c in df.columns]
                st.dataframe(df[cols].reset_index(drop=True), use_container_width=True)
        elif key == "dash_tx":              render_transactions()
        elif key == "dash_notifs":          render_notifications_center()
        elif key == "dash_chat":            render_messaging_center()
        # admin (somente se admin)
        elif is_admin and key == "admin_users":       admin_render_users()
        elif is_admin and key == "admin_analytics":   admin_render_analytics()
        elif is_admin and key == "admin_disputes":    admin_render_disputes()
        elif is_admin and key == "admin_comm":        admin_render_comm()
        elif is_admin and key == "admin_promo":       admin_render_promo()
        elif is_admin and key == "admin_clients":     admin_render_clients()
        elif is_admin and key == "admin_site":        admin_render_site()
        else:
            st.info("This section is available to Admins.")

    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.route == "rfp":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    render_rfp(with_topbar=False)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.error("Unknown route. Returning to landing…")
    nav("landing")

# ---- pending nav hook ----
if st.session_state.get("_pending_nav"):
    del st.session_state["_pending_nav"]
    st.rerun()
