import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image



# App Header with Logo
img = Image.open("./Logo/trans_bg.png")
col1, col2 = st.columns([1, 4])
with col1:
    st.image(img, width=100)  # Logo
with col2:
    st.title("Smart Resume Analyzer")

# Custom Navigation Bar using option_menu
selected = option_menu(
    menu_title=None,  # Hide Title
    options=["🏠 Home", "📝 Register", "🔑 Login", "👤 Normal User", "⚙️ Admin"],
    icons=["house", "pencil", "key", "person", "gear"],
    menu_icon="cast",  # Optional Menu Icon
    default_index=0,
   
)

# Navigation Logic
if selected == "🏠 Home":
    st.subheader("Welcome to Home Page")
elif selected == "📝 Register":
    st.subheader("Register Page")
elif selected == "🔑 Login":
    st.subheader("Login Page")
elif selected == "👤 Normal User":
    st.subheader("Normal User Dashboard")
elif selected == "⚙️ Admin":
    st.subheader("Admin Panel")
