import streamlit as st
from streamlit_option_menu import option_menu

from pages.launch_chatbot import render_chatbot_app
from pages.chat_groups import render_chat_groups_page
from pages.chat_history import render_chat_history_page

# Configure page with proper icon and wide layout
st.set_page_config(
    page_title="Personal Chat Admin",
    page_icon="resources/images/personal_chatbot_ai_friend.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# # Reduce top whitespace sitewide
# st.markdown(
#     """
#     <style>
#     .block-container {padding-top: 0.5rem; padding-bottom: 1rem;}
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# Horizontal top menu spanning full width
selected_top = option_menu(
    None,
    ["Home", "Chat Groups", "Chat History", "Settings"],
    icons=["house", "view-list", "clock-history", "gear"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    # styles={
    #     "container": {"padding": "0!important", "max-width": "100%", "margin": "0"},
    #     "icon": {"font-size": "18px"},
    #     "nav-link": {"font-size": "16px", "padding": "6px 16px", "margin": "0 2px"},
    #     "nav-link-selected": {"background-color": "#f0f2f6"},
    # },
)

# Navigate to other pages when selected
if selected_top == "Chat Groups":
    try:
        render_chat_groups_page()
        st.stop()
    except Exception as e:
        st.error(f"Navigation failed to Chat Groups: {e}")
elif selected_top == "Chat History":
    try:
        render_chat_history_page()
        st.stop()
    except Exception as e:
        st.error(f"Navigation failed to Chat History: {e}")
elif selected_top == "Home":
    try:
        render_chatbot_app(use_internal_sidebar=True)
        st.stop()
    except Exception as e:
        st.error(f"Navigation failed to Chatbot: {e}")
    # Render chatbot embedded, with its internal left menu living in-page
elif selected_top == "Settings":
    # Placeholder; remain on Home for now
    st.write("Settings page")
    st.stop()
else:
    pass