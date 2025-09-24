import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date

# -------------------------------------------------------------
# VIP – Landing + Auth (USERNAME) + Dashboard + Marketplace + RFP Wizard
# -------------------------------------------------------------

st.set_page_config(
    page_title="VIP • Venue Intelligence Platform",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =====================
#   DASH MENU (sem o Wizard)
# =====================
DASH_SECTIONS = [
    "🔎 Search & Filter Marketplace",
    "🗂️ RFP Submission History",
    "💳 Transaction History",
    "🔔 Notification Center",   # fica entre Transaction e Chat
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

def _seed_notifications():
    return [
        {"id": 1, "title": "Payment confirmed",     "body": "Catering - $500 received.",       "ts": "2025-09-19 16:05", "ntype": "success", "read": True},
        {"id": 2, "title": "RFP response received", "body": "Vertex 161 sent a proposal.",     "ts": "2025-09-22 10:12", "ntype": "info",    "read": False},
        {"id": 3, "title": "New message",           "body": "Venue Harbor replied in chat.",   "ts": "2025-09-18 09:21", "ntype": "message", "read": False},
    ]

def _seed_transactions():
    return pd.DataFrame(
        [
            ["2025-09-15", "Harbor 412",  "Venue Booking",     300, "Completed", "TXN-001"],
            ["2025-09-17", "Helix 238",   "AV Support",        150, "Completed", "TXN-002"],
            ["2025-09-20", "Radiant 179", "Catering Deposit",  500, "Pending",   "TXN-003"],
            ["2025-09-22", "Vertex 161",  "Photography",       150, "Refunded",  "TXN-004"],
        ],
        columns=["date", "counterparty", "service", "amount", "status", "ref"],
    )

if "notifications" not in st.session_state:
    st.session_state.notifications = _seed_notifications()
if "transactions" not in st.session_state:
    st.session_state.transactions = _seed_transactions()
if "rfp_history" not in st.session_state:
    st.session_state.rfp_history = []

# Messaging seed
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

if "mail" not in st.session_state:
    st.session_state.mail = _seed_mail()
if "mail_folder" not in st.session_state:
    st.session_state.mail_folder = "Inbox"
if "mail_thread" not in st.session_state:
    st.session_state.mail_thread = st.session_state.mail["Inbox"][0]["id"] if st.session_state.mail["Inbox"] else None

# Painéis flutuantes / badge
if "help_open" not in st.session_state:
    st.session_state.help_open = False
if "notif_open" not in st.session_state:
    st.session_state.notif_open = False
if "help_chat" not in st.session_state:
    st.session_state.help_chat = [
        {"by":"Carol","ts":"2025-09-22 09:00","text":"Hi! Need help with RFPs or vendors?"},
    ]
if "notif_badge_cleared" not in st.session_state:
    st.session_state.notif_badge_cleared = False

# =====================
# CONSTANTS / PATHS
# =====================
from pathlib import Path

ROLE_OPTIONS = ["For-Profit (Client)", "Non-Profit", "Venue", "Vendor"]
IMG_WIDTH = 600

ROOT = Path(__file__).resolve().parent
LOGO_PATH = ROOT / "assets" / "logo.png"
DATA_PATH = ROOT / "data" / "marketplace_clean_numeric.csv"


# =====================
#        STYLES
# =====================
st.markdown(
    """
    <style>
      /* ---------- Painel flutuante (base) ---------- */
      .vip-float {
        position: fixed !important;
        right: 16px !important;
        width: 420px !important;
        height: 540px !important;
        background: #fff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 30px rgba(0,0,0,.18) !important;
        z-index: 100000 !important;
        overflow: hidden !important;
        pointer-events: auto !important;
      }
      .notif-panel { top: 86px !important; }
      .help-panel  { top: 646px !important; }

      .float-header {
        padding: 10px 14px; border-bottom: 1px solid #eee;
        font-weight: 700; background: #111827; color: #fff;
      }
      .float-body {
        padding: 10px 14px; background:#f9fafb; overflow-y: auto;
        height: calc(540px - 48px - 72px); /* total - header - footer */
      }
      .float-footer { padding: 10px 14px; border-top: 1px solid #eee; background:#fff; }

      .bubble-u { background:#e5f0ff; padding:8px 10px; border-radius:10px; margin:6px 0; display:inline-block; }
      .bubble-a { background:#dcfce7; padding:8px 10px; border-radius:10px; margin:6px 0; display:inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================
#      HELPERS
# =====================

from base64 import b64encode
import mimetypes

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
    # mapa de checkboxes persistente
    if "notif_read_map" not in st.session_state:
        st.session_state.notif_read_map = {n["id"]: n.get("read", False) for n in st.session_state.notifications}
    else:
        for n in st.session_state.notifications:
            st.session_state.notif_read_map.setdefault(n["id"], n.get("read", False))

# =====================
#      SECTIONS
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

        # nova notificação + reexibir badge
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

def render_topbar_right(scope: str = "dashboard"):
    # init flags
    if "notif_open" not in st.session_state:
        st.session_state.notif_open = False
    if "notif_badge_cleared" not in st.session_state:
        st.session_state.notif_badge_cleared = False
    if "help_open" not in st.session_state:
        st.session_state.help_open = False

    left, right = st.columns([7, 3], gap="small")
    with right:
        b1, b2 = st.columns(2, gap="small")

        # ===== Notifications =====
        unread = unread_count()
        show_badge = (unread > 0) and (not st.session_state.notif_badge_cleared)
        notif_label = f"🔔 Notifications ({unread})" if show_badge else "🔔 Notifications"

        if b1.button(notif_label, key=f"btn_notif_{scope}", use_container_width=True):
            # limpa o badge na primeira interação
            st.session_state.notif_badge_cleared = True
            # alterna abrir/fechar o painel flutuante
            st.session_state.notif_open = not st.session_state.notif_open
            st.rerun()

        # ===== Support (Carol) =====
        support_open = st.session_state.help_open
        support_label = "💬 Support" if not support_open else "💬 Hide chat"
        if b2.button(support_label, key=f"btn_support_{scope}", use_container_width=True):
            st.session_state.help_open = not support_open
            st.rerun()



# =====================
# Support Panel (bottom-right)
# =====================

# --- HELP TEXT (Carol) ---
HELP_WELCOME = (
    "Welcome! I'm Carol, your virtual assistant. "
    "I can help you find venues and vendors, draft and send RFPs, "
    "and answer questions about your transactions. How can I help today?"
)
HELP_PLACEHOLDER = "Type your question here or describe what you need…"


def render_help_panel():
    """Render Carol's chat panel (no footer/minimize buttons)."""
    if not st.session_state.get("help_open", False):
        return

    st.markdown(
        f"""
        <div id="vip-help"
             style="
               position: fixed;
               bottom: 24px; right: 24px;
               width: 380px; height: 460px;
               background: #ffffff;
               border: 1px solid #e5e7eb;
               border-radius: 12px;
               box-shadow: 0 16px 40px rgba(0,0,0,.24);
               z-index: 999999;
               overflow: hidden;">
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
# Painel de Notificações (flutuante no topo-direito)
# =====================
def render_notif_panel():
    if not st.session_state.get("notif_open", False):
        return

    _ensure_notif_read_map()
    read_map = st.session_state.notif_read_map
    notifs = sorted(st.session_state.notifications, key=_notif_sort_key, reverse=True)

    st.markdown(
        """
        <div style="
            position: fixed; top: 86px; right: 16px;
            width: 420px; height: 540px;
            background: #fff; border: 1px solid #e5e7eb;
            border-radius: 12px; padding: 0;
            box-shadow: 0 12px 30px rgba(0,0,0,.18);
            z-index: 100000; overflow: hidden;">
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

        # Rodapé com botões
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

## =====================
#        ROUTES
# =====================
if st.session_state.route == "landing":
    st.markdown("<div class='vip-wrap'><section class='vip-hero'>", unsafe_allow_html=True)
    st.markdown("<span class='vip-badge'>🤝 FreeFuse × Sophist</span>", unsafe_allow_html=True)
    st.markdown("<div class='vip-title'>Venue Intelligence Platform</div>", unsafe_allow_html=True)
    st.markdown("<div class='vip-sub'>The operating system for nonprofit events — plan, book, and measure impact.</div>", unsafe_allow_html=True)

    # 👉 Imagem centralizada (usa helper que converte para base64 e centra via flex)
    # def render_centered_image(path: str, max_width_px: int = 800):  # (definido nos helpers)
    render_centered_image(LOGO_PATH, max_width_px=900)

    # CTAs
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
        role = st.radio("Select your profile type", ROLE_OPTIONS, horizontal=True)
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

        # Header opcional por papel
        if "render_role_header" in globals():
            render_role_header(user["role"])
        else:
            st.markdown("### Dashboard")
            st.caption(f"Profile: **{user['role']}**")

        # Conteúdo principal (menu persistente)
        render_common_dashboard()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.route == "rfp":
    st.markdown("<div class='vip-wrap'>", unsafe_allow_html=True)
    render_rfp(with_topbar=True, scope="rfp_page")
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.error("Unknown route. Returning to landing…")
    nav("landing")

# ---- pending nav hook ----
if st.session_state.get("_pending_nav"):
    del st.session_state["_pending_nav"]
    st.rerun()

# === Painéis flutuantes (somente suporte; sino não abre nada) ===
render_help_panel()

