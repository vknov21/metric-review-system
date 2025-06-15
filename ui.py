import streamlit as st
from config import METRIC, REVIEWERS_SHORTHAND
from db_storage.db_queries import get_reviewers_finalised_cols
from metric_utils import page_has_refreshed, fetch_initials, get_refresh_browser_ids
from template import get_tooltip_css
from init import get_initialization_choices
from handler import confirmation_dialog


@st.cache_data
def get_all_metric_initials():
    # Map full metric to short names and the reverse of it
    return {li: fetch_initials(li) for li in METRIC}
    # reversed_metrics_initials = {v: k for k, v in all_metrics_initials.items()}


def confirm_rating(*args, **kwargs):
    browser_id, _ = get_refresh_browser_ids() 
    """Validates and triggers the confirmation dialog."""
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


def create_header(container_parent, cnt, user_names, self):
    if self:
        metric_col, names_col, self_col = container_parent.columns([1.8, cnt, 1], border=False, vertical_alignment="center")
    else:
        cnt = 1
        metric_col, names_col = container_parent.columns([1.8, 1], border=False, vertical_alignment="center")
    with metric_col:
        with st.columns(1, border=True)[0]:
            st.markdown("**METRIC**")
    with names_col:
        all_names_col = st.columns(cnt, border=True)
        for idx in range(len(all_names_col)):
            with all_names_col[idx]:
                st.markdown(f"**{user_names[idx][1].capitalize()}**")
    if self:
        with self_col:  # pyright:ignore
            with st.columns(1, border=True)[0]:
                st.markdown(f"<font style='color:magenta;'><b>{self.capitalize()}<b></font>", unsafe_allow_html=True)


def create_txt_entries(columns_cnt_list, container, all_metrics_initials, cnt, user_names, reviewer_save_vars, reviewer, self, page_refreshed, error_users_field):
    for metric in METRIC:
        metric_shorthand = all_metrics_initials[metric]
        with container:
            metric_col, *names_col = container.columns(columns_cnt_list, vertical_alignment="center")
            with metric_col:
                st.markdown(f"**{metric}**")
            for idx in range(len(names_col)):
                if self:
                    user_name = user_names[idx][1] if idx < cnt else self
                else:
                    user_name = user_names[idx][1]
                value, disabled = "", False
                # If reviewer has already reviewed a user_name, replace the values with '*'
                if user_name in reviewer_save_vars["finalised"]:
                    value, disabled = "*", True
                with names_col[idx]:
                    key = f"{user_name}_{metric_shorthand}"
                    if value != "*":
                        if key not in reviewer_save_vars:
                            value = ""
                        else:
                            value = reviewer_save_vars[key] if page_refreshed is True and reviewer_save_vars.get(key) != "" else st.session_state.get(key, "")
                    value = st.text_input("rating", placeholder=user_name.capitalize(), max_chars=3, label_visibility="collapsed", key=key, value=value, disabled=disabled)
                    if value and value != '*':
                        msg = validate_input(key, reviewer)
                        if msg:
                            error_users_field.add(user_name)
                            st.markdown(get_tooltip_css(msg), unsafe_allow_html=True)


def create_metric_mapping(reviewer, reviewer_mapping=REVIEWERS_SHORTHAND):
    """Render metric entry table with validations and UI layout."""
    all_metrics_initials = get_all_metric_initials()
    user_to_id_map, metric_shorthand_to_id_map = get_initialization_choices()
    error_users_field = set()
    page_refreshed = page_has_refreshed()
    all_users_name: dict = reviewer_mapping.copy()
    if reviewer not in st.const_vars["input_save"]:
        if reviewer in all_users_name:
            st.const_vars["input_save"][reviewer] = {"finalised": get_reviewers_finalised_cols(user_to_id_map[reviewer_mapping[reviewer]])}
        else:
            st.const_vars["input_save"][reviewer] = {"finalised": []}
    reviewer_save_vars = st.const_vars["input_save"][reviewer]

    # Separate the reviewer from others that needs to be reviewed
    pop_self = all_users_name.pop(reviewer, None)
    all_users_name = list(all_users_name.items())
    total_cnt_removing_self = len(reviewer_mapping) - 1

    # Table header layout
    container_parent = st.container(border=True)
    create_header(container_parent, total_cnt_removing_self, all_users_name, pop_self)

    # Metric input table rows
    container = container_parent.container()
    columns_cnt_list = [1.8] + [1] * total_cnt_removing_self + [1]
    create_txt_entries(columns_cnt_list, container, all_metrics_initials, total_cnt_removing_self, all_users_name, reviewer_save_vars, reviewer, pop_self, page_refreshed, error_users_field)

    # Confirmation row corresponding to each user's name
    metric_col, *names_col = container_parent.columns(columns_cnt_list, vertical_alignment="center")
    with metric_col:
        st.markdown("<font style='color:green;'><b>[ Confirmation ]</b></font>", unsafe_allow_html=True)
    for idx in range(len(names_col)):
        if pop_self:
            user_name = all_users_name[idx][1] if idx < total_cnt_removing_self else pop_self
        else:
            user_name = all_users_name[idx][1]
        disabled = False
        if user_name in reviewer_save_vars["finalised"]:
            disabled = True
        with names_col[idx]:
            st.button("✅ Done...", key=user_name, on_click=confirm_rating, args=(user_name, error_users_field, metric_shorthand_to_id_map),
                      use_container_width=True, type="secondary", disabled=disabled)

    # Persist review inputs
    reviewer_save_vars.update(st.session_state.to_dict())
