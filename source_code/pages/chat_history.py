import streamlit as st

# Robust imports to work whether running as a package or script
try:
    from config.models import ChatHistoryCreate, ChatHistoryUpdate
except ModuleNotFoundError:
    from source_code.config.models import ChatHistoryCreate, ChatHistoryUpdate

try:
    from crud import (
        list_chat_history,
        create_chat_history,
        update_chat_history,
        delete_chat_history,
    )
except ModuleNotFoundError:
    from source_code.crud import (
        list_chat_history,
        create_chat_history,
        update_chat_history,
        delete_chat_history,
    )


def render_chat_history_page():
    # Flash banner (shared via session_state)
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
        st.session_state.flash = None

    # Inline editing state
    if "edit_history_id" not in st.session_state:
        st.session_state.edit_history_id = None

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
                    st.session_state.flash = ("success", f"Chat History record {int(new_id)} created successfully.")
                    st.session_state.ch_action_tab = "List"
                    st.rerun()
                else:
                    st.error("Failed to create record")
        else:
            st.subheader("Chat History (max 50)")
            records = list_chat_history(limit=50)

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
                    group_id_val = c3.number_input("", min_value=0, step=1, value=int(r.chat_group_id or 0),
                                                   key=f"ch_group_{r.id}")
                    inquiry_val = c4.text_area("", value=r.user_inquiry, key=f"ch_inq_{r.id}")
                    resp_val = c5.text_area("", value=r.assistant_response, key=f"ch_resp_{r.id}")
                    ref_val = c6.number_input("", min_value=0, step=1, value=int(r.reference_id or 0),
                                              key=f"ch_ref_{r.id}")
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
