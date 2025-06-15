import streamlit as st
from config import DB_NAME, METRIC_DESCRIPTIVE, REVIEWERS_SHORTHAND
from db_storage.db_queries import get_initialized_user_requests, delete_all_db_data, check_if_db_exists, \
    initialize_tables_for_db, get_user_to_id_map, get_metric_to_id_map, insert_all_data
from metric_utils import fetch_initials
from exceptions import DatabaseDoesNotExist


@st.cache_data
def get_initialization_choices():
    initialization_choices = eval(st.const_vars["initialization_choices"])
    user_to_id_map: dict = initialization_choices["user_id_mapping"]
    metric_shorthand_to_id_map: dict = initialization_choices["metric_id_mapping"]
    return user_to_id_map, metric_shorthand_to_id_map


@st.cache_data
def initialize_const_vars(key, value):
    """Utility to initialize constant variables on the `st` object."""
    if not hasattr(st, "const_vars"):
        setattr(st, "const_vars", {})
    st.const_vars.setdefault(key, value)


def insert_into_db():
    st.const_vars["initialization_choices"] = ''
    initialization_choices = {}
    # Inserts metric data with name and description onto the DB
    insert_all_data(metric_data=METRIC_DESCRIPTIVE.items())
    # Inserts users name and username (shorthand) declared as the Const onto the DB
    insert_all_data(user_data=REVIEWERS_SHORTHAND.items())
    # Assigns user to id mapping, which will be a dictionary in form {username: id, username2: id2, ...}
    initialization_choices["user_id_mapping"] = get_user_to_id_map()
    metric_full_to_id_map = get_metric_to_id_map()
    initialization_choices["metric_id_mapping"] = {fetch_initials(k): v for k, v in metric_full_to_id_map.items()}
    st.const_vars["initialization_choices"] = str(initialization_choices)


@st.cache_data
def initiated_request_verif():
    if st.const_vars.get('db_verified', 'False') != 'True':
        try:
            st.browser_access_info = {}
            check_if_db_exists()
        except DatabaseDoesNotExist:
            initialize_tables_for_db()
            insert_into_db()
        else:
            accept = 'y'
            # accept = input(f"The database named {DB_NAME} already exists. To overwrite that DB press 'y' or 'n' to continue with the current DB in the state that it is in: ")
            st.const_vars['initialized_from_db'] = 'False'
            st.const_vars["browser_reviewer"] = {}
            st.const_vars["initialization_choices"] = "{}"

            if accept in ['y', 'Y']:
                delete_all_db_data()
                insert_into_db()
            elif accept in ['n', 'N']:
                print("Continuing on existing DB entries")
                initialization_choices = {}
                initialization_choices["user_id_mapping"] = get_user_to_id_map()
                metric_full_to_id_map = get_metric_to_id_map()
                initialization_choices["metric_id_mapping"] = {fetch_initials(k): v for k, v in metric_full_to_id_map.items()}
                st.const_vars["initialization_choices"] = str(initialization_choices)
                browser_access_info = get_initialized_user_requests()
                st.browser_access_info = {k: {v: set()} for k, v in browser_access_info.items()}
                st.const_vars["browser_reviewer"] = {v: k for k, v in browser_access_info.items()}
                st.const_vars['initialized_from_db'] = 'True'
            else:
                print("\nNot a valid response. Exiting...")
                st.stop()
        finally:
            st.const_vars['db_verified'] = 'True'
