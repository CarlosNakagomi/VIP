# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from base64 import b64encode
import mimetypes
import random

# -------------------------------------------------------------
# VIP – Landing + Auth (USERNAME) + Dashboard + Marketplace + RFP Wizard + ADMIN
# -------------------------------------------------------------

st.set_page_config(
    page_title="VIP • Venue Intelligence Platform",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================
#   DASH MENU
# =====================
DASH_SECTIONS = [
    "🔎 Search & Filter Marketplace",
    "🗂️ RFP Submission History",
    "💳 Transaction History",
    "🔔 Notification Center",
    "💬 Chat / Messaging Center",
]
if "dash_section" not in st.session_state or st.session_state.dash_section not in DASH_SECTIONS:
    st.session_state.dash_section = DASH_SECTIONS[0]

# =====================
#   SESSION DEFAULTS
# =====================
if "route" not in st.session_state:
    st.session_state.route = "landing"
if "users" not in st.session_state:
    st.session_state.users = {}
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ---- Seeds (notifications, transactions, mail) ----
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

# Painéis / badge
if "help_open" not in st.session_state:
    st.session_state.help_open = False
if "notif_open" not in st.session_state:
    st.session_state.notif_open = False
if "help_chat" not in st.session_state:
    st.session_state.help_chat = [{"by":"Carol","ts":"2025-09-22 09:00","text":"Hi! Need help with RFPs or vendors?"}]
if "notif_badge_cleared" not in st.session_state:
    st.session_state.notif_badge_cleared = False

# =====================
# CONSTANTS / PATHS
# =====================
ROLE_OPTIONS = ["For-Profit (Client)", "Non-Profit", "Venue", "Vendor"]
ADMIN_ROLE = "Admin"
IMG_WIDTH = 600

ROOT = Path(__file__).resolve().parent
LOGO_PATH = ROOT / "assets" / "logo.png"
DATA_PATH = ROOT / "data" / "marketplace_clean_numeric.csv"

# =====================
# STYLES (theme inspirado no Builder)
# =====================
st.markdown(
    """
    <style>
      :root{
        --vip-bg:#0b1220; --vip-card:#0f172a; --vip-soft:#111827; --vip-soft2:#0b132a;
        --vip-ink:#e5e7eb; --vip-ink2:#94a3b8; --vip-accent:#22c55e; --vip-accent-2:#38bdf8;
        --vip-danger:#ef4444; --vip-warn:#f59e0b;
      }
      .vip-wrap{padding:0 8px 40px;}
      .vip-hero{display:flex;flex-direction:column;align-items:center;gap:10px;margin:20px auto;}
      .vip-badge{display:inline-block;padding:6px 10px;border-radius:9999px;background:#0ea5e9;color:white;font-size:12px;}
      .vip-title{font-size:34px;font-weight:800;color:#111827;}
      .vip-sub{font-size:15px;color:#374151;margin-bottom:8px;}
      .vip-ctas{display:flex;gap:12px;justify-content:center;width:100%;max-width:720px;margin:12px 0;}
      .vip-footer{color:#6b7280;text-align:center;margin-top:18px;}
      .muted{color:#6b7280;font-size:12px;}
      /* Cards métricos */
      .kpi{background:#ecfdf5;border:1px solid #d1fae5;border-radius:14px;padding:16px;box-shadow:0 6px 14px rgba(0,0,0,.08);}
      .kpi h4{margin:0;color:#065f46;font-weight:700;font-size:13px}
      .kpi .v{margin-top:6px;color:#047857;font-weight:800;font-size:26px}
      /* Charts container */
      .vip-card{background:white;border:1px solid #e5e7eb;border-radius:12px;padding:14px;box-shadow:0 6px 14px rgba(0,0,0,.06);}
      /* Float panels */
      .bubble-u { background:#e5f0ff; padding:8px 10px; border-radius:10px; margin:6px 0; display:inline-block; }
      .bubble-a { background:#dcfce7; padding:8px 10px; border-radius:10px; margin:6px 0; display:inline-block; }
    </style>
    """, unsafe_allow_html=True
)

# =====================
# HELPERS
# =====================
def render_centered_image(path: str, max_width_px: int = 800):
    p = Path(path)
    if p.exists():
        data = p.read_bytes()
        mime = mimetypes.guess_type(p.name)[0] or "image/png"
        b64 = b64encode(data).decode()
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:18px 0;">
              <img src="data:{mime};base64,{b64}"
                   style="max-width:{max_width_px}px;width:100%;height:auto;border-radius:6px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;align-items:center;width:100%;margin:18px 0;">
              <img src="https://via.placeholder.com/1200x480?text=Venue+Intelligence+Platform"
                   style="max-width:{max_width_px}px;width:100%;height:auto;border-radius:6px;" />
            </div>
            """,
            unsafe_allow_html=True,
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
def _notif_sort_key(n):
    try:
        return datetime.strptime(n.get("ts", ""), "%Y-%m-%d %H:%M")
    except Exception:
        return datetime.min
def _ensure_notif_read_map():
    if "notif_read_map" not in st.session_state:
        st.session_state.notif_read_map = {n["id"]: n.get("read", False) for n in st.session_state.notifications}
    else:
        for n in st.session_state.notifications:
            st.session_state.notif_read_map.setdefault(n["id"], n.get("read", False))

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

def render_rfp(with_topbar: bool = True, scope: str = "rfp_page"):
    if with_topbar:
        render_topbar_right(scope=scope)

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
#  NOTIFICATIONS
# =====================
def render_notifications():
    st.subheader("🔔 Notification Center")
    _ensure_notif_read_map()
    read_map = st.session_state.notif_read_map
    notifs = sorted(st.session_state.notifications, key=_notif_sort_key, reverse=True)

    if not notifs:
        st.info("No notifications yet.")
        return

    updated_map = dict(read_map)
    for n in notifs:
        with st.container(border=True):
            cols = st.columns([8, 2])
            tone = "🆕" if not read_map.get(n["id"], False) else "✅"
            cols[0].markdown(
                f"**{tone} {n.get('title','(no title)')}**  \n"
                f"{n.get('body','')}  \n"
                f"<span class='muted'>{n.get('ts','')}</span>",
                unsafe_allow_html=True,
            )
            chk = cols[1].checkbox(
                "Read",
                value=read_map.get(n["id"], False),
                key=f"notif_read_{n['id']}",
            )
            updated_map[n["id"]] = chk

    st.session_state.notif_read_map = updated_map
    for n in st.session_state.notifications:
        n["read"] = updated_map.get(n["id"], False)

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
#  TOP BAR (notifications + support)
# =====================
def render_topbar_right(scope: str = "dashboard"):
    if "notif_open" not in st.session_state:
        st.session_state.notif_open = False
    if "notif_badge_cleared" not in st.session_state:
        st.session_state.notif_badge_cleared = False
    if "help_open" not in st.session_state:
        st.session_state.help_open = False

    left, right = st.columns([7, 3], gap="small")
    with right:
        b1, b2 = st.columns(2, gap="small")
        unread = unread_count()
        show_badge = (unread > 0) and (not st.session_state.notif_badge_cleared)
        notif_label = f"🔔 Notifications ({unread})" if show_badge else "🔔 Notifications"
        if b1.button(notif_label, key=f"btn_notif_{scope}", use_container_width=True):
            st.session_state.notif_badge_cleared = True
            st.session_state.notif_open = not st.session_state.notif_open
            st.rerun()
        support_open = st.session_state.help_open
        support_label = "💬 Support" if not support_open else "💬 Hide chat"
        if b2.button(support_label, key=f"btn_support_{scope}", use_container_width=True):
            st.session_state.help_open = not support_open
            st.rerun()

# =====================
# Support panel (Carol)
# =====================
HELP_WELCOME = (
    "Welcome! I'm Carol, your virtual assistant. "
    "I can help you find venues and vendors, draft and send RFPs, "
    "and answer questions about your transactions. How can I help today?"
)
HELP_PLACEHOLDER = "Type your question here or describe what you need…"
def render_help_panel():
    if not st.session_state.get("help_open", False):
        return
    st.markdown(
        f"""
        <div id="vip-help"
             style="position: fixed; bottom: 24px; right: 24px; width: 380px; height: 460px;
               background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
               box-shadow: 0 16px 40px rgba(0,0,0,.24); z-index: 999999; overflow: hidden;">
          <div style="padding:12px 16px; border-bottom:1px solid #eee; font-weight:700;">
            💬 Carol — Virtual Assistant
          </div>
          <div style="padding:12px 16px; height: calc(460px - 56px); overflow:auto;">
            <p style="margin:0 0 8px 0; color:#374151;"><i>{HELP_WELCOME}</i></p>
            <div style="margin-top:10px; padding:12px; background:#f3f4f6; border-radius:8px;">
              {HELP_PLACEHOLDER}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =====================
#  FLOAT NOTIF PANEL
# =====================
def render_notif_panel():
    if not st.session_state.get("notif_open", False):
        return
    _ensure_notif_read_map()
    read_map = st.session_state.notif_read_map
    notifs = sorted(st.session_state.notifications, key=_notif_sort_key, reverse=True)

    st.markdown(
        """
        <div style="position: fixed; top: 86px; right: 16px; width: 420px; height: 540px;
            background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 0;
            box-shadow: 0 12px 30px rgba(0,0,0,.18); z-index: 100000; overflow: hidden;">
            <div style="padding:10px 14px; background:#111827; color:#fff; font-weight:700;">
                🔔 Notifications
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown(
            "<div style='height: 472px; width: 420px; position: fixed; top: 134px; right: 16px; "
            "background:#f9fafb; padding:10px 14px; overflow-y:auto; z-index:100001; border-radius:0 0 12px 12px;'>",
            unsafe_allow_html=True,
        )
        updated_map = dict(read_map)
        if not notifs:
            st.info("No notifications yet.")
        else:
            for n in notifs:
                with st.container(border=True):
                    cols = st.columns([8, 2])
                    tone = "🆕" if not read_map.get(n["id"], False) else "✅"
                    cols[0].markdown(
                        f"**{tone} {n.get('title','(no title)')}**  \n"
                        f"{n.get('body','')}  \n"
                        f"<span class='muted'>{n.get('ts','')}</span>",
                        unsafe_allow_html=True,
                    )
                    chk = cols[1].checkbox(
                        "Read",
                        value=read_map.get(n["id"], False),
                        key=f"notif_float_read_{n['id']}",
                    )
                    updated_map[n["id"]] = chk
        st.session_state.notif_read_map = updated_map
        for n in st.session_state.notifications:
            n["read"] = updated_map.get(n["id"], False)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            "<div style='position: fixed; right: 16px; top: 86px; width:420px; height:540px; z-index:100002; pointer-events:none;'>"
            "<div style='position:absolute; bottom:8px; left:14px; right:14px; display:flex; gap:8px; pointer-events:auto;'>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        if c1.button("Mark all as read", key="notif_mark_all_btn"):
            for n in st.session_state.notifications:
                n["read"] = True
            st.session_state.notif_read_map = {n["id"]: True for n in st.session_state.notifications}
            st.rerun()
        if c2.button("Close", key="notif_close_btn"):
            st.session_state.notif_open = False
            st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

# =====================
#  RFP HISTORY
# =====================
def render_rfp_history():
    st.subheader("🗂️ RFP Submission History")
    rows = st.session_state.get("rfp_history", [])
    if not rows:
        st.info("No RFP submissions yet.")
        return
    df = pd.DataFrame(rows)

    c1, c2 = st.columns([2,1])
    with c1:
        q = st.text_input("Search (title / target / city)")
    with c2:
        date_from = st.date_input("From date", value=None)

    if q:
        ql = q.lower()
        df = df[df.apply(lambda r:
                         ql in str(r.get("title","")).lower() or
                         ql in str(r.get("target_name","")).lower() or
                         ql in str(r.get("target_city","")).lower(), axis=1)]
    if date_from:
        df = df[pd.to_datetime(df["submitted_at"]) >= pd.to_datetime(date_from)]
    df = df.sort_values(by="submitted_at", ascending=False)

    cols = ["submitted_at","title","target_name","target_type","target_city","budget","target_date","price","target_contact"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].reset_index(drop=True), use_container_width=True)

# =====================
#  COMMON DASHBOARD
# =====================
def render_common_dashboard():
    render_topbar_right(scope="dashboard")
    section = st.radio(
        "Navigation",
        options=DASH_SECTIONS,
        horizontal=True,
        label_visibility="collapsed",
        key="dash_section",
    )
    st.write("")
    if section == "🔎 Search & Filter Marketplace":
        render_marketplace()
    elif section == "🗂️ RFP Submission History":
        render_rfp_history()
    elif section == "💳 Transaction History":
        render_transactions()
    elif section == "🔔 Notification Center":
        render_notifications()
    elif section == "💬 Chat / Messaging Center":
        render_messaging_center()

# =====================
#  -------- ADMIN --------
# =====================

# Seeds Admin
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

# Admin state
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

def _require_admin():
    u = st.session_state.get("current_user")
    if not u or u.get("role") != ADMIN_ROLE:
        st.error("Admin access required.")
        return False
    return True

def _user_rows_df():
    rows = []
    for uname, info in st.session_state.users.items():
        rows.append({
            "username": uname,
            "role": info.get("role"),
            "full_name": info.get("full_name",""),
            "contact": info.get("contact",""),
            "status": info.get("status","Active"),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["username","role","full_name","contact","status"])

# Helpers gráficos (parecidos com o Builder, valores fictícios porém coerentes)
def _demo_series(days=14, base=100, volatility=15):
    now = datetime.now()
    data = []
    val = base
    for i in range(days):
        val = max(0, val + random.randint(-volatility, volatility))
        data.append({"date": (now - timedelta(days=days-i)).strftime("%Y-%m-%d"), "value": val})
    return pd.DataFrame(data)

def _transactions_by_status_df():
    tx = st.session_state.transactions.copy()
    if tx.empty:
        return pd.DataFrame({"status": [], "amount": []})
    return tx.groupby("status", as_index=False)["amount"].sum().sort_values("amount", ascending=False)

def render_admin_panel():
    if not _require_admin():
        return

    st.title("🧠 Admin Superpanel (Internal Ops)")
    tabs = st.tabs(["👥 Users","📈 Analytics","🚩 Disputes","📣 Communications","🚀 Promo/Boost","📦 Data Clients"])

    # ---------- 1) Users ----------
    with tabs[0]:
        st.subheader("User Management")
        df = _user_rows_df()
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

    # ---------- 2) Analytics ----------
    with tabs[1]:
        st.subheader("Analytics & Reporting Hub")
        tx = st.session_state.transactions.copy()
        rfps = pd.DataFrame(st.session_state.rfp_history) if st.session_state.get("rfp_history") else pd.DataFrame(columns=["submitted_at"])

        total_rev = int(tx.loc[tx["status"]=="Completed","amount"].sum()) if not tx.empty else 0
        pending = int(tx.loc[tx["status"]=="Pending","amount"].sum()) if not tx.empty else 0
        completed = int((tx["status"]=="Completed").sum()) if not tx.empty else 0

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"<div class='kpi'><h4>Revenue (Completed)</h4><div class='v'>${total_rev:,.0f}</div></div>", unsafe_allow_html=True)
        with k2:
            st.markdown(f"<div class='kpi'><h4>Pending Payments</h4><div class='v'>${pending:,.0f}</div></div>", unsafe_allow_html=True)
        with k3:
            st.markdown(f"<div class='kpi'><h4>Completed Orders</h4><div class='v'>{completed}</div></div>", unsafe_allow_html=True)
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
            by_status = _transactions_by_status_df()
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

    # ---------- 3) Disputes ----------
    with tabs[2]:
        st.subheader("Flagged Content / Disputes")
        disp = st.session_state.admin_disputes
        if not disp:
            st.info("No disputes.")
        else:
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
            if st.button("Export disputes CSV"):
                df_disp = pd.DataFrame(st.session_state.admin_disputes)
                st.download_button("Download", data=df_disp.to_csv(index=False).encode("utf-8"),
                                   file_name="disputes.csv", mime="text/csv")

    # ---------- 4) Communications ----------
    with tabs[3]:
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

    # ---------- 5) Promo/Boost ----------
    with tabs[4]:
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

    # ---------- 6) Data Clients ----------
    with tabs[5]:
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

# =====================
#        ROUTES
# =====================
if st.session_state.route == "landing":
    st.markdown("<div class='vip-wrap'><section class='vip-hero'>", unsafe_allow_html=True)
    st.markdown("<span class='vip-badge'>🤝 FreeFuse × Sophist</span>", unsafe_allow_html=True)
    st.markdown("<div class='vip-title'>Venue Intelligence Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='vip-sub'>The operating system for nonprofit events — plan, book, and measure impact.</div>", unsafe_allow_html=True)
    render_centered_image(LOGO_PATH, max_width_px=900)
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
        role = st.radio("Select your profile type", ROLE_OPTIONS + [ADMIN_ROLE], horizontal=True)
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
            # Admin link
            if user.get("role") == ADMIN_ROLE:
                st.divider()
                if st.button("🧠 Admin Superpanel"):
                    nav("admin")

        st.markdown("### Dashboard")
        st.caption(f"Profile: **{user['role']}**")
        render_common_dashboard()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.route == "rfp":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    render_rfp(with_topbar=True, scope="rfp_page")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.route == "admin":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    render_topbar_right(scope="admin")
    render_admin_panel()
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.error("Unknown route. Returning to landing…")
    nav("landing")

# ---- pending nav hook ----
if st.session_state.get("_pending_nav"):
    del st.session_state["_pending_nav"]
    st.rerun()

# === Float support panel ===
render_help_panel()
# === Float notifications ===
render_notif_panel()
