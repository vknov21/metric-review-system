import streamlit as st
from config import REVIEWERS_SHORTHAND
from metric_utils import get_refresh_browser_ids
from db_storage.db_queries import insert_all_data
from init import get_initialization_choices


@st.dialog("Confirm")
def confirmation_dialog(msg, name, metrics):
    """Confirmation dialog for submitting the review."""
    browser_id, refresh_id = get_refresh_browser_ids()
    user_to_id_map, _ = get_initialization_choices()
    st.markdown(msg)
    button1, button2 = st.columns(2)
    if button1.button("Confirm", type="primary", use_container_width=True):
        st.session_state.confirm_dialog = True
        db_entry_list = []
        reviewer = st.const_vars["browser_reviewer"][browser_id]
        st.const_vars["input_save"][reviewer]["finalised"].append(name)
        user_id = user_to_id_map[REVIEWERS_SHORTHAND[reviewer]]
        ratee_id = user_to_id_map[name]
        metric_to_score = {}
        for metric_shrt in metrics:
            metric_id = metrics[metric_shrt]
            key = f"{name}_{metric_shrt}"
            val = st.session_state.get(key, "")
            metric_to_score[metric_id] = int(val) if val != "" else None
        for metric_id in metric_to_score:
            db_entry_list.append([user_id, ratee_id, metric_id, metric_to_score[metric_id]])
        insert_all_data(rating_data=db_entry_list)
        st.rerun()  # Closes the dialog box
    elif button2.button("Cancel", type="secondary", use_container_width=True):
        st.session_state.confirm_dialog = False
        st.rerun()  # Closes the dialog box
