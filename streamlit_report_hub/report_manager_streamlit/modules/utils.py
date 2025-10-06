import streamlit as st 
import uuid 
import os 



def safe_rerun():
    """
    Try to rerun the Streamlit script in a backward/forward compatible way.
    This implementation intentionally does NOT call safe_rerun() recursively.
    """
    # 1) try old experimental API if available
    try:
        fn = getattr(st, "experimental_rerun", None)
        if callable(fn):
            fn()
            return
    except Exception:
        # ignore and try next
        pass

    # 2) try newer API
    try:
        fn2 = getattr(st, "rerun", None)
        if callable(fn2):
            fn2()
            return
    except Exception:
        pass

    # 3) fallback: nudge query params to force a rerun (no recursive call)
    try:
        params = st.experimental_get_query_params()
        params["_rerun"] = str(uuid.uuid4())
        st.experimental_set_query_params(**params)
        return
    except Exception:
        # final fallback: tell the user to refresh the page
        st.info("Please refresh the page to continue (Ctrl-R / Cmd-R).")



def clear_form_and_rerun(keys: list[str] = None):
    """
    Clears the specified Streamlit session_state keys (form fields) and reruns the app.
    If keys=None, just reruns the app.
    """
    if keys:
        for key in keys:
            if key in st.session_state:
                st.session_state[key] = None  # or "" depending on input type
    safe_rerun()



def get_user_dict():
    """Ensure session_state.user is always a dict."""
    if "user" not in st.session_state or st.session_state.user is None:
        st.session_state.user = {}
    return st.session_state.user
