import streamlit as st

# Robust imports to work whether running as a package or script
try:
    from config.models import ChatGroupDtlCreate, ChatGroupDtlUpdate
except ModuleNotFoundError:
    from source_code.config.models import ChatGroupDtlCreate, ChatGroupDtlUpdate

try:
    from crud import (
        list_chat_groups,
        create_chat_group,
        update_chat_group,
        delete_chat_group,
    )
except ModuleNotFoundError:
    from ..crud import (
        list_chat_groups,
        create_chat_group,
        update_chat_group,
        delete_chat_group,
    )


def render_chat_groups_page():
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
    if "edit_group_id" not in st.session_state:
        st.session_state.edit_group_id = None

    # Submenu
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
                    st.session_state.flash = ("success", f"Chat Group {int(new_id)} created successfully.")
                    st.session_state.cg_action_tab = "List"
                    st.rerun()
                else:
                    st.error("Failed to create group. Check logs and DB connectivity.")
        else:
            st.subheader("Chat Groups (max 50)")
            groups = list_chat_groups(active_only=bool(active_only))[:50]

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
