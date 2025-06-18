import time
import streamlit as st
from config import REVIEWERS_SHORTHAND
from db_storage.db_queries import insert_all_data, get_reviewers_finalised_cols, get_counts_of_reviewed, get_average_scores
import sys
import re
import pathlib
from init import initialize_const_vars, initiated_request_verif, get_initialization_choices
from metric_utils import get_refresh_browser_ids, get_reviewers_shorthand
from template import get_self_review_css
from ui import create_metric_mapping, create_remaining_review_watch


if __name__ == "__main__":
    # Enforce running via `streamlit run` command
    command = ' '.join(sys.orig_argv)
    filename = pathlib.Path(__file__).name
    pattern = rf"streamlit.*?run.*?{re.escape(filename)}"
    if not re.search(pattern, command):
        print("ERROR: This script is intended to be run with Streamlit, and not directly with Python.")
        print("USAGE: streamlit run <file_name>.py")
        sys.exit(1)


# Streamlit page configuration
st.set_page_config(page_title="Reviewer", page_icon="random", layout="wide", menu_items=None)
initialize_const_vars("input_save", {})
initiated_request_verif()

# Initializes for global access, and also to verify if the Browser is in Incognito/Private Window,
# which fails to get the 'ajs_anonymous_id' and requires a one time refresh
browser_id, refresh_id = get_refresh_browser_ids()

# Initializes browser access info, if not already present
for c in REVIEWERS_SHORTHAND:
    if c not in st.browser_access_info:
        st.browser_access_info[c] = {}

user_to_id_map, metric_shorthand_to_id_map = get_initialization_choices()


def store_selection(*args, **kwargs):
    """Assign the selected reviewer name to the browser session."""
    global browser_id
    if "browser_reviewer" not in st.const_vars:
        st.const_vars["browser_reviewer"] = {}

    if browser_id in st.const_vars["browser_reviewer"]:
        st.warning("User is already logged in with a Reviewer Name. Resuming the session", icon=":material/warning:")
    elif args[0] in st.const_vars["browser_reviewer"].values():
        st.error(f"User as {args[0]} is already registered with the system. Use other as the Reviewer Name", icon=":material/error:")
    elif args[0]:
        user_id = user_to_id_map[REVIEWERS_SHORTHAND[args[0]]]
        st.const_vars["browser_reviewer"][browser_id] = args[0]
        insert_all_data(auth_data=(user_id, browser_id))


reviewer_sel = st.columns([1, 0.2])

# Reviewer selection if not already assigned
if not st.const_vars.get("browser_reviewer") or not st.const_vars["browser_reviewer"].get(browser_id):
    with reviewer_sel[0]:
        selection = st.selectbox(label="Reviewing User", options=REVIEWERS_SHORTHAND, index=None, label_visibility="collapsed",
                                 placeholder="Select your Name")

    with reviewer_sel[1]:
        st.button("Confirm", key="confirm", on_click=store_selection, type="primary", args=(selection,))

# Display reviewer identity and metric entry form
if st.const_vars.get("browser_reviewer") and st.const_vars["browser_reviewer"].get(browser_id):
    reviewer = st.const_vars["browser_reviewer"][browser_id]
    st.markdown(get_self_review_css(reviewer), unsafe_allow_html=True)
    all_to_review = get_reviewers_shorthand(reviewer)
    user_to_id_map, metric_shorthand_to_id_map = get_initialization_choices()
    reviewers_id = user_to_id_map[REVIEWERS_SHORTHAND[reviewer]]
    st.const_vars["input_save"][reviewer] = {"finalised": get_reviewers_finalised_cols(reviewers_id)}
    if reviewer in st.const_vars["input_save"] and sorted(all_to_review.values()) == sorted(st.const_vars["input_save"][reviewer]["finalised"]):
        not_started, pending_reviewers, completed_users = get_counts_of_reviewed()
        if not not_started and not pending_reviewers:
            get_average_scores([])
            st.stop()
        else:
            create_remaining_review_watch(pending_reviewers, not_started)
    else:
        create_metric_mapping(reviewer, all_to_review)
