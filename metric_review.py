# Import necessary libraries
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit import runtime
from config.config import DB_NAME, METRIC, METRIC_DESCRIPTIVE, REVIEWERS_SHORTHAND as choices
from db_operations import get_initialized_user_requests, delete_all_db_data, get_db_path, \
    check_if_db_exists, insert_all_data, initialize_tables_for_db, DB_PATH, get_user_to_id_map
from exceptions import DatabaseDoesNotExist
import sys
import re
import pathlib

# Streamlit page configuration
st.set_page_config(page_title="Reviewer", page_icon="random", layout="wide", menu_items=None)


def get_request_obj():
    """Fetch the HTTP request object to extract client-specific info."""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return ""
        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return ""
    except Exception:
        return ""
    return session_info.request


def get_refresh_browser_ids():
    """Extract a unique browser identifier and refresh session key."""
    request = get_request_obj()
    try:
        browser_id = request._cookies['ajs_anonymous_id']._value  # unique browser identifier for a given browser session. Changes for Incognito/Private window
    except KeyError:
        raise Exception("Currently Private or Incognito Tab requires a refresh of the page to start working")
    refresh_id = request.headers._dict['Sec-Websocket-Key']   # changes on page refresh
    return browser_id, refresh_id


def page_has_refreshed():
    """Detects if the page has been refreshed or a new browser is getting registered.

        Returns: [None | True | False]:
        .... None : A new browser entry detected
        .... True : The existing browser had a page refresh
        .... False: The page wasn't refreshed but the streamlit had re-executed
    """
    browser_id, refresh_id = get_refresh_browser_ids()
    # There are two variables in use, for the browser_info:
    # .... 1) st.const_vars["browser_reviewer"]: It gets initialized, as soon as someone selects a reviewer name,
    #         and it creates dictionary of keys having browser_id and the user's name (as per the key in the choices) as value
    # .... 2) st.browser_access_info[reviewer] : It gets initialized in this function and stores the data on browser_id and refresh_id
    #         corresponding to the reviewer
    try:
        # Checks if any user has already started a review session
        reviewer = st.const_vars.get("browser_reviewer")
        if not reviewer:
            return False
    except Exception:
        return False

    # This may never get hit, but added it as an assurance. It gets initialized for the provided names during the app run itself
    if not hasattr(st, "browser_access_info"):
        return False

    browser_access_info = st.browser_access_info
    # Since browser_reviewer already exists, so, reviewer entry corresponding to the current browser_id exists as well
    reviewer = reviewer[browser_id]

    # The browser_reviewer gets initialized here
    if not browser_access_info[reviewer]:
        # Initialize browser access info on first load
        browser_access_info[reviewer] = {browser_id: set([refresh_id])}
    else:
        # If the same reviewer is accessing through the browser that they have't registered, don't reinitialize
        if browser_id not in browser_access_info[reviewer]:
            # If it's the first time. Returning None means browser change
            return None
        for sess in browser_access_info[reviewer][browser_id]:
            if sess == refresh_id:
                return False  # Refresh ID already exists
        print(f"Page Refreshed for reviewer: {reviewer}")
        st.browser_access_info[reviewer][browser_id].add(refresh_id)
        return True


st.browser_access_info = {}
if 'initialize_from_db' not in st.session_state or st.session_state.initialize_from_db is False:
    st.browser_access_info = get_initialized_user_requests()

# Initializes for global access, and also to verify if the Browser is in Incognito/Private Window,
# which fails to get the 'ajs_anonymous_id' and requires a one time refresh
browser_id, refresh_id = get_refresh_browser_ids()

# Initializes browser access info, if not already present
for c in choices:
    if c not in st.browser_access_info:
        st.browser_access_info[c] = {}

try:
    check_if_db_exists()
except DatabaseDoesNotExist:
    pass
else:
    accept = input(f"The database named {DB_NAME} already exists. Either add a new DB entry in config.py file or press 'y' if you wish to delete all the entries and start over: ")
    if accept not in ['y', 'Y']:
        print("Exiting, as the user hasn't selected 'y' and wishes to keep the data stored in the current DB")
        exit(1)
    delete_all_db_data()


if 'initialization_choices' not in st.session_state:
    st.session_state.initialization_choices = {}
    # Inserts metric data with name and description onto the DB
    insert_all_data(metric_data=METRIC_DESCRIPTIVE.items())
    # Inserts users name and username (shorthand) declared as the Const onto the DB
    choices_rev = {v: k for k, v in choices}
    insert_all_data(user_data=choices.items())
    # Assigns user to id mapping, which will be a dictionary in form {username: id, username2: id2, ...}
    st.session_state.initialization_choices["user_id_mapping"] = get_user_to_id_map()

user_to_id_map: dict = st.session_state.initialization_choices["user_id_mapping"]


def initialize_const_vars(key, value):
    """Utility to initialize constant variables on the `st` object."""
    if not hasattr(st, "const_vars"):
        setattr(st, "const_vars", {})
    st.const_vars.setdefault(key, value)


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
        st.const_vars["browser_reviewer"][browser_id] = args[0]
        insert_all_data(auth_data=(user_id, browser_id))


@st.dialog("Confirm")
def confirmation_dialog(msg, name, metrics):
    """Confirmation dialog for submitting the review."""
    global browser_id
    st.markdown(msg)
    button1, button2 = st.columns(2)
    if button1.button("Confirm", type="primary", use_container_width=True):
        st.session_state.confirm_dialog = True
        reviewer = st.const_vars["browser_reviewer"][browser_id]
        st.const_vars["input_save"][reviewer]["finalised"].append(name)
        st.rerun()  # Closes the dialog box
    elif button2.button("Cancel", type="secondary", use_container_width=True):
        st.session_state.confirm_dialog = False
        st.rerun()  # Closes the dialog box


def confirm_rating(*args, **kwargs):
    """Validates and triggers the confirmation dialog."""
    global browser_id
    reviewer = st.const_vars["browser_reviewer"][browser_id]
    user_name, error_users_field, metrics = args
    if user_name in st.const_vars["input_save"][reviewer]["finalised"]:
        st.error(f"You have already submitted your rating for User: '{user_name.capitalize()}'")
        return
    if user_name in error_users_field:
        st.error("Resolve errors first, before proceeding", icon=":material/error:")
        return
    confirmation_dialog(f'''
        Are you sure you want to Submit the review for '{user_name.capitalize()}'?  
        **NOTE:** You won't be able to modify it afterwards.
    ''', user_name, metrics)


def validate_input(*args, **kwargs):
    """Ensures that the input is a float and is between 1 and 10."""
    global reversed_metrics_initials
    val: float = st.session_state.get(args[0])
    msg = None
    try:
        val = float(val)
    except ValueError:
        msg = "Input should be a floating point"
    else:
        if val < 1 or val > 10:
            msg = "Range should be 1 to 10"
    return msg


def fetch_initials(text):
    """Convert metric text to lowercase initials to get unique key for the text field"""
    text = text.replace('&', 'a').replace('/', ' ').replace('-', ' ')
    text = text.split(' ')
    sel = ''
    for li in text:
        ascii_code = ord(li[0])
        if ascii_code < 92 and ascii_code > 64:
            ascii_code += 32
        if ascii_code > 96 and ascii_code < 124:
            sel += chr(ascii_code)
    return sel


def create_metric_mapping(reviewer):
    """Render metric entry table with validations and UI layout."""
    error_users_field = set()
    page_refreshed = page_has_refreshed()
    all_users_name = choices.copy()
    if reviewer not in st.const_vars["input_save"]:
        st.const_vars["input_save"][reviewer] = {"finalised": get_reviewers_finalised_cols()}
    reviewer_save_vars = st.const_vars["input_save"][reviewer]

    # Separate the reviewer from others that needs to be reviewed
    pop_self = all_users_name.pop(reviewer)
    all_users_name = list(all_users_name.items())
    total_cnt_removing_self = len(choices) - 1

    # Table header layout
    container_parent = st.container(border=True)
    metric_col, names_col, self_col = container_parent.columns([1.8, total_cnt_removing_self, 1], border=False, vertical_alignment="center")
    with metric_col:
        with st.columns(1, border=True)[0]:
            st.markdown("**METRIC**")
    with names_col:
        all_names_col = st.columns(total_cnt_removing_self, border=True)
        for idx in range(len(all_names_col)):
            with all_names_col[idx]:
                st.markdown(f"**{all_users_name[idx][1].capitalize()}**")
    with self_col:
        with st.columns(1, border=True)[0]:
            st.markdown(f"<font style='color:magenta;'><b>{pop_self.capitalize()}<b></font>", unsafe_allow_html=True)

    # Metric input table rows
    columns_cnt_list = [1.8] + [1] * total_cnt_removing_self + [1]
    container = container_parent.container()
    for metric in METRIC:
        metric_shorthand = all_metrics_initials[metric]
        with container:
            metric_col, *names_col = container.columns(columns_cnt_list, vertical_alignment="center")
            with metric_col:
                st.markdown(f"**{metric}**")
            for idx in range(len(names_col)):
                user_name = all_users_name[idx][1] if idx < total_cnt_removing_self else pop_self
                value, disabled = "", False
                # If reviewer has already reviewed a user_name, replace the values with '*'
                if user_name in reviewer_save_vars["finalised"]:
                    value, disabled = "*", True
                with names_col[idx]:
                    key = f"{user_name}_{metric_shorthand}"
                    if value != "*":
                        value = reviewer_save_vars[key] if page_refreshed is True and reviewer_save_vars.get(key) != "" else st.session_state.get(key, "")
                    value = st.text_input("rating", placeholder=user_name.capitalize(), max_chars=3, label_visibility="collapsed", key=key, value=value, disabled=disabled)
                    if value and value != '*':
                        msg = validate_input(key, reviewer)
                        if msg:
                            error_users_field.add(user_name)
                            st.markdown(f"""
                                <style>
                                    .tooltip {{
                                        # display: inline-block;
                                        cursor: pointer;
                                        margin-left: 0%;
                                        margin-top: -18px;
                                        border-radius: 9px;
                                        border: 3px;
                                        border-style: ridge;
                                        border-color: darkred;
                                        text-align: center;
                                        background-color: #dc143c;
                                    }}

                                    .tooltip .tooltiptext {{
                                        visibility: hidden;
                                        width: max-content;
                                        background-color: #dc143c;
                                        color: #fff;
                                        border-radius: 6px;
                                        padding: 8px 10px;
                                        position: absolute;
                                        left: 0%;
                                        z-index: 1;
                                        opacity: 0;
                                        transition: opacity 0.3s;
                                        font-size: 14px;
                                        white-space: normal;
                                    }}

                                    .tooltip:hover .tooltiptext {{
                                        visibility: visible;
                                        opacity: 1;
                                    }}
                                </style>
                                <div class="tooltip">❌ <font style='color:#ffa07a;'>ERROR</font>
                                    <span class="tooltiptext" style='top:-55px; left:40px'>{msg}</span>
                                </div>
                            """, unsafe_allow_html=True)

    # Confirmation row corresponding to each user's name
    metric_col, *names_col = container_parent.columns(columns_cnt_list, vertical_alignment="center")
    with metric_col:
        st.markdown("<font style='color:green;'><b>[ Confirmation ]</b></font>", unsafe_allow_html=True)
    for idx in range(len(names_col)):
        user_name = all_users_name[idx][1] if idx < total_cnt_removing_self else pop_self
        disabled = False
        if user_name in reviewer_save_vars["finalised"]:
            disabled = True
        with names_col[idx]:
            st.button("✅ Done...", key=user_name, on_click=confirm_rating, args=(user_name, error_users_field, reversed_metrics_initials.keys()),
                      use_container_width=True, type="secondary", disabled=disabled)

    # Persist review inputs
    reviewer_save_vars.update(st.session_state.to_dict())


# Map full metric to short names and the reverse of it
all_metrics_initials = {li: fetch_initials(li) for li in METRIC}
reversed_metrics_initials = {v: k for k, v in all_metrics_initials.items()}


if __name__ == "__main__":
    # Enforce running via `streamlit run` command
    command = ' '.join(sys.orig_argv)
    filename = pathlib.Path(__file__).name
    pattern = rf"streamlit.*?run.*?{re.escape(filename)}"
    if not re.search(pattern, command):
        print("ERROR: This script is intended to be run with Streamlit, and not directly with Python.")
        print("USAGE: streamlit run <file_name>.py")
        sys.exit(1)

reviewer_sel = st.columns([1, 0.2])
initialize_const_vars("input_save", {})

# Reviewer selection if not already assigned
if not st.const_vars.get("browser_reviewer") or not st.const_vars["browser_reviewer"].get(browser_id):
    with reviewer_sel[0]:
        selection = st.selectbox(label="Reviewing User", options=choices, index=None, label_visibility="collapsed",
                                 placeholder="Select your Name")

    with reviewer_sel[1]:
        st.button("Confirm", key="confirm", on_click=store_selection, type="primary", args=(selection,))

# Display reviewer identity and metric entry form
if st.const_vars.get("browser_reviewer") and st.const_vars["browser_reviewer"].get(browser_id):
    reviewer = st.const_vars["browser_reviewer"][browser_id]
    st.markdown(f"""
        <style>
            div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {{
                position: fixed;
                top: 4.2rem;
                width: 89.6%;
                opacity: 0.7;
                background-color: black;
                z-index: 999;
            }}
        </style>
        <div class="fixed-header">
            <center><h6 style='color: white;'>The reviewer is: <font style='color:magenta;'>{reviewer}</font></h4></center>
        </div>
    """, unsafe_allow_html=True)
    create_metric_mapping(reviewer)
