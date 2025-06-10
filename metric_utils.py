# Import necessary libraries
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit import runtime


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
