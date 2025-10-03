import streamlit as st
from typing import Optional

from config.models import (
    ChatGroupDtlCreate,
    ChatGroupDtlUpdate,
    ChatHistoryCreate,
    ChatHistoryUpdate,
)
from crud import (
    list_chat_groups,
    get_chat_group,
    create_chat_group,
    update_chat_group,
    delete_chat_group,
    list_chat_history,
    get_chat_history,
    create_chat_history,
    update_chat_history,
    delete_chat_history,
)

st.set_page_config(page_title="Personal Chat Admin", layout="wide")

st.title("Database Admin - Personal Chat")

# Initialize session state for inline editing
if "edit_group_id" not in st.session_state:
    st.session_state.edit_group_id = None
if "edit_history_id" not in st.session_state:
    st.session_state.edit_history_id = None

# Flash message support (shown at top and cleared after display)
if "flash" not in st.session_state:
    st.session_state.flash = None
if st.session_state.flash:
    kind, msg = st.session_state.flash
    if kind == "success":
        st.success(msg)
    elif kind == "error":
        st.error(msg)
    else:
        st.info(msg)
    # Clear flash after showing
    st.session_state.flash = None

# Horizontal main menu
tab_groups, tab_history = st.tabs(["Chat Groups", "Chat History"])

# ------------------------------
# Chat Groups Tab
# ------------------------------
with tab_groups:
    left, right = st.columns([1, 5])
    with left:
        action_cg = st.radio("Action", ["List", "Create"], index=0, key="cg_action_tab")
        active_only = None
        if action_cg == "List":
            active_only = st.checkbox("Show only active", value=False, key="cg_active_only")

    with right:
        if action_cg == "Create":
            st.subheader("Create Chat Group")
            with st.form("create_group_form"):
                new_id = st.number_input("ID", min_value=1, step=1)
                user_id = st.number_input("User ID", min_value=1, step=1)
                group_name = st.text_input("Group Name")
                group_desc = st.text_area("Group Description")
                is_active = st.checkbox("Is Active", value=True)
                submitted = st.form_submit_button("Create")
            if submitted:
                payload = ChatGroupDtlCreate(
                    id=int(new_id),
                    user_id=int(user_id),
                    group_name=group_name or None,
                    group_desc=group_desc or None,
                    is_active=bool(is_active),
                )
                rows = create_chat_group(payload)
                if rows:
                    # Redirect to List with confirmation banner
                    st.session_state.flash = ("success", f"Chat Group {int(new_id)} created successfully.")
                    st.session_state.cg_action_tab = "List"
                    st.rerun()
                else:
                    # Stay on Create and show error
                    st.error("Failed to create group. Check logs and DB connectivity.")
        else:
            st.subheader("Chat Groups (max 50)")
            # Fetch and cap to 50
            groups = list_chat_groups(active_only=bool(active_only))
            groups = groups[:50]

            # Scrollable list container
            st.markdown('<div style="max-height:500px; overflow-y:auto;">', unsafe_allow_html=True)

            # Header
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1, 1, 2, 3, 1, 2, 1, 1])
            h1.markdown("**ID**")
            h2.markdown("**User**")
            h3.markdown("**Name**")
            h4.markdown("**Description**")
            h5.markdown("**Active**")
            h6.markdown("**Created**")
            h7.markdown("**Edit**")
            h8.markdown("**Delete**")

            for g in groups:
                editing = st.session_state.edit_group_id == g.id
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1, 1, 2, 3, 1, 2, 1, 1])
                c1.write(g.id)
                if editing:
                    user_id_val = c2.number_input("", min_value=1, step=1, value=g.user_id, key=f"cg_user_{g.id}")
                    name_val = c3.text_input("", value=g.group_name or "", key=f"cg_name_{g.id}")
                    desc_val = c4.text_input("", value=g.group_desc or "", key=f"cg_desc_{g.id}")
                    active_val = c5.checkbox("", value=g.is_active, key=f"cg_act_{g.id}")
                    c6.write(str(g.created_ts) if g.created_ts else "-")
                    save = c7.button("Save", key=f"cg_save_{g.id}")
                    cancel = c8.button("Cancel", key=f"cg_cancel_{g.id}")
                    if save:
                        payload = ChatGroupDtlUpdate(
                            user_id=int(user_id_val),
                            group_name=name_val or None,
                            group_desc=desc_val or None,
                            is_active=bool(active_val),
                        )
                        rows = update_chat_group(g.id, payload)
                        if rows:
                            st.success(f"Group {g.id} updated")
                        else:
                            st.info("No changes or update failed")
                        st.session_state.edit_group_id = None
                        st.rerun()
                    if cancel:
                        st.session_state.edit_group_id = None
                        st.rerun()
                else:
                    c2.write(g.user_id)
                    c3.write(g.group_name or "")
                    c4.write(g.group_desc or "")
                    c5.write("Yes" if g.is_active else "No")
                    c6.write(str(g.created_ts) if g.created_ts else "-")
                    edit = c7.button("Edit", key=f"cg_edit_{g.id}")
                    delete = c8.button("Delete", key=f"cg_del_{g.id}")
                    if edit:
                        st.session_state.edit_group_id = g.id
                        st.rerun()
                    if delete:
                        rows = delete_chat_group(g.id)
                        if rows:
                            st.success(f"Group {g.id} deleted")
                        else:
                            st.error("Failed to delete group")
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------
# Chat History Tab
# ------------------------------
with tab_history:
    left, right = st.columns([1, 5])
    with left:
        action_ch = st.radio("Action", ["List", "Create"], index=0, key="ch_action_tab")
    with right:
        if action_ch == "Create":
            st.subheader("Create Chat History Record")
            with st.form("create_history_form"):
                new_id = st.number_input("ID (bigint)", min_value=1, step=1)
                user_id = st.number_input("User ID", min_value=1, step=1, value=1)
                user_inquiry = st.text_area("User Inquiry")
                assistant_response = st.text_area("Assistant Response")
                reference_id = st.number_input("Reference ID (bigint)", min_value=0, step=1, value=0)
                chat_group_id = st.number_input("Chat Group ID", min_value=0, step=1, value=0)
                submitted = st.form_submit_button("Create")
            if submitted:
                payload = ChatHistoryCreate(
                    id=int(new_id),
                    user_id=int(user_id),
                    user_inquiry=user_inquiry,
                    assistant_response=assistant_response,
                    reference_id=int(reference_id) if reference_id else None,
                    chat_group_id=int(chat_group_id) if chat_group_id else None,
                )
                rows = create_chat_history(payload)
                if rows:
                    # Redirect to List with confirmation banner
                    st.session_state.flash = ("success", f"Chat History record {int(new_id)} created successfully.")
                    st.session_state.ch_action_tab = "List"
                    st.rerun()
                else:
                    # Stay on Create and show error
                    st.error("Failed to create record")
        else:
            st.subheader("Chat History (max 50)")
            records = list_chat_history(limit=50)

            # Scrollable list container
            st.markdown('<div style="max-height:500px; overflow-y:auto;">', unsafe_allow_html=True)

            # Header
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2, 1, 2, 2, 2, 2, 1, 1])
            h1.markdown("**ID / Created**")
            h2.markdown("**User**")
            h3.markdown("**Group**")
            h4.markdown("**Inquiry**")
            h5.markdown("**Response**")
            h6.markdown("**Refs**")
            h7.markdown("**Edit**")
            h8.markdown("**Delete**")

            for r in records:
                editing = st.session_state.edit_history_id == r.id
                c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 1, 2, 2, 2, 2, 1, 1])
                c1.write(f"{r.id}\n{str(r.created_ts)}")
                if editing:
                    user_id_val = c2.number_input("", min_value=1, step=1, value=r.user_id, key=f"ch_user_{r.id}")
                    group_id_val = c3.number_input("", min_value=0, step=1, value=int(r.chat_group_id or 0), key=f"ch_group_{r.id}")
                    inquiry_val = c4.text_area("", value=r.user_inquiry, key=f"ch_inq_{r.id}")
                    resp_val = c5.text_area("", value=r.assistant_response, key=f"ch_resp_{r.id}")
                    ref_val = c6.number_input("", min_value=0, step=1, value=int(r.reference_id or 0), key=f"ch_ref_{r.id}")
                    save = c7.button("Save", key=f"ch_save_{r.id}")
                    cancel = c8.button("Cancel", key=f"ch_cancel_{r.id}")
                    if save:
                        payload = ChatHistoryUpdate(
                            user_id=int(user_id_val),
                            user_inquiry=inquiry_val,
                            assistant_response=resp_val,
                            reference_id=int(ref_val) if ref_val else None,
                            chat_group_id=int(group_id_val) if group_id_val else None,
                        )
                        rows = update_chat_history(r.id, payload)
                        if rows:
                            st.success(f"Record {r.id} updated")
                        else:
                            st.info("No changes or update failed")
                        st.session_state.edit_history_id = None
                        st.rerun()
                    if cancel:
                        st.session_state.edit_history_id = None
                        st.rerun()
                else:
                    c2.write(r.user_id)
                    c3.write(r.chat_group_id or "-")
                    c4.write((r.user_inquiry or "")[0:80] + ("…" if len(r.user_inquiry or "") > 80 else ""))
                    c5.write((r.assistant_response or "")[0:80] + ("…" if len(r.assistant_response or "") > 80 else ""))
                    c6.write(r.reference_id or "-")
                    edit = c7.button("Edit", key=f"ch_edit_{r.id}")
                    delete = c8.button("Delete", key=f"ch_del_{r.id}")
                    if edit:
                        st.session_state.edit_history_id = r.id
                        st.rerun()
                    if delete:
                        rows = delete_chat_history(r.id)
                        if rows:
                            st.success(f"Record {r.id} deleted")
                        else:
                            st.error("Failed to delete record")
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
