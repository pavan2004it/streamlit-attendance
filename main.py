import os
from datetime import date
import streamlit as st
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.requests_client import OAuth2Session
from dotenv import load_dotenv
import sqlite3

# Load environment variables and set up OAuth client
load_dotenv('.env')
REDIRECT_URI = os.environ['REDIRECT_URI']
OKTA_CLIENT_ID = os.environ['OKTA_CLIENT_ID']
OKTA_CLIENT_SECRET = os.environ['OKTA_CLIENT_SECRET']
OKTA_AUTHORIZATION_ENDPOINT = os.environ['OKTA_AUTHORIZATION_ENDPOINT']
OKTA_TOKEN_ENDPOINT = os.environ['OKTA_TOKEN_ENDPOINT']
OKTA_USERINFO_ENDPOINT = os.environ['OKTA_USERINFO_ENDPOINT']
client = OAuth2Session(OKTA_CLIENT_ID, OKTA_CLIENT_SECRET, redirect_uri=REDIRECT_URI)

conn = sqlite3.connect('attendance.db')
c = conn.cursor()


def create_attendance_table():
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
             (name TEXT, email TEXT, date TEXT)''')
    conn.commit()


def show_emails():
    c.execute("SELECT email FROM attendance")
    return [row[0] for row in c.fetchall()]

# Custom CSS
def load_css():
    st.markdown("""
  <style>
  .big-font {
      font-size:30px !important;
      font-weight: bold;
  }
  .stButton>button {
      color: #4F8BF9;
      border-radius: 50px;
      height: 3em;
      width: 100%;
  }
  </style>
  """, unsafe_allow_html=True)


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login():
    st.markdown("<h1 style='text-align: center;'>Welcome to AYS Attendance App</h1>", unsafe_allow_html=True)

    authorization_url, state = client.create_authorization_url(
        OKTA_AUTHORIZATION_ENDPOINT,
        scope="openid"
    )
    st.session_state.auth_url = authorization_url

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button("Login with Okta", st.session_state.auth_url)


def callback():
    if 'code' in st.query_params:
        code = st.query_params['code']
        try:
            with st.spinner("Logging you in..."):
                token = client.fetch_token(
                    OKTA_TOKEN_ENDPOINT,
                    code=code,
                    scope="openid",
                    grant_type="authorization_code"
                )
                userinfo = client.get(OKTA_USERINFO_ENDPOINT).json()
                st.session_state['user'] = userinfo
                st.session_state.logged_in = True
                st.success("Successfully logged in!")
        except OAuthError as e:
            st.error(f"OAuth error: {e}")


def logout():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.query_params.clear()
            st.rerun()


def user_attendance():
    st.title("User Attendance")
    with st.form("attendance_form", clear_on_submit=True):
        options = show_emails()
        name = st.text_input("Name")
        email = st.selectbox("Select Email", options)
        today = st.date_input("Select Date", value=None)
        present_date = date.today().strftime("%Y-%m-%d")
        st.text(f"Date: {present_date}")
        submit_button = st.form_submit_button("Submit Attendance")
    if submit_button:
        if name and email:  # Check if name and email are not empty
            create_attendance_table()
            c.execute("INSERT INTO attendance VALUES (?, ?, ?)", (name, email, today))
            conn.commit()
            st.success("Attendance recorded successfully!")
        else:
            st.error("Please enter both name and email.")


login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
user_attendance_page = st.Page(user_attendance, title="User Attendance")
reports = st.Page("tools/reports.py", title="Reports", icon="📊")


def main():
    load_css()
    # App header
    if 'code' in st.query_params:
        callback()

    if st.session_state.logged_in:
        st.sidebar.markdown(f"Welcome, {st.session_state['user'].get('name', 'Admin')}!")
        pg = st.navigation(
            {
                "Account": [logout_page],
                "Tools": [reports],
            }
        )
    else:
        pg = st.navigation([login_page, user_attendance_page])

    pg.run()


if __name__ == "__main__":
    main()




