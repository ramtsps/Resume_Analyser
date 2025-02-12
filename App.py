import streamlit as st
import nltk
import spacy
nltk.download('stopwords')
spacy.load('en_core_web_sm')
import sqlite3
import pandas as pd
import base64, random
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, resume_videos, interview_videos
# import pafy
import yt_dlp 
import plotly.express as px
import hashlib
from streamlit_option_menu import option_menu

# import youtube_dl

connection = sqlite3.connect("db.sqlite3")
cursor = connection.cursor()



#new function



# Create Users Table (if not exists)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
""")
connection.commit()

# Function to Hash Passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to Verify Password
def check_password(hashed_password, user_password):
    return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

# Register Function
def register_user(name, email, password):
    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, hash_password(password)))
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Email already exists

# Login Function
def login_user(email, password):
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    if user and check_password(user[3], password):
        return user  # Return user details
    return None

# Initialize session state for authentication
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_name"] = None
    st.session_state["user_email"] = None





#exit

def fetch_yt_video(link):
    """Fetches YouTube video title using yt-dlp"""
    ydl_opts = {"quiet": True, "format": "best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        return info.get("title", "Unknown Title")


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf">'
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("**Courses & Certificates🎓 Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


# connection = pymysql.connect(host='localhost', user='root', password='')
# cursor = connection.cursor()



def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "INSERT INTO " + DB_table_name + """
    VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

    rec_values = (
    name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
   
    connection.commit()


st.set_page_config(
    page_title="Smart Resume Analyzer",
    page_icon='./Logo/trans_bg.png',
)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_name" not in st.session_state:
    st.session_state["user_name"] = ""
if "user_email" not in st.session_state:
    st.session_state["user_email"] = ""

def run():
    
    img = Image.open("./Logo/trans_bg.png")

    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(img, width=100)  # Logo
    with col2:
        st.title("Smart Resume Analyzer")

    # ✅ Sidebar Navigation using option_menu

    
    # ✅ Styled Sidebar Navigation (With Custom Background Colors)
    with st.sidebar:
        # If redirected, use the stored page
        if "redirect_to" in st.session_state and st.session_state["redirect_to"]:
            choice = st.session_state["redirect_to"]
            st.session_state["redirect_to"] = None  # Reset after use

        if st.session_state["logged_in"]:
            choice = option_menu(
            menu_title="🚀 Quick Access",
            options=["🏠 Home", "👤 Normal User", "⚙️ Admin", "ℹ️ About", "📞 Contact", "🚪 Logout"],
            # icons=["house", "person", "gear", "info", "phone", "door-open"],
            menu_icon="menu",
            default_index=0,
            styles={
                "container": {
                    "padding": "5px",
                   "background": "linear-gradient(to bottom, #00c6ff, #0072ff)",  # ✅ Fresh Green Gradient
                    "border-radius": "10px",
                    "box-shadow": "0px 0px 10px rgba(255, 255, 255, 0.2)",
                },
                "menu-title": {  
                    "font-size": "22px",
                    "font-weight": "bold",
                    "background": "#152d2b",  # ✅ Dark Background for Title
                    "color": "#ffffff",
                    "padding": "10px",
                    "border-radius": "8px",
                    "text-align": "center",
                },
                "nav-link": {
                    "font-size": "18px",
                    "text-align": "left",
                    "color": "#ffffff",
                    "padding": "10px",
                    "border-radius": "8px",
                    "transition": "all 0.3s ease-in-out",
                },
                "nav-link-hover": {
                    "background": "linear-gradient(to right, #ff512f, #dd2476)",  # ✅ Fiery Red-Pink Hover
                    "color": "#ffffff",
                    "transform": "scale(1.05)",
                },
                "nav-link-selected": {
                    "background": "#ff9800",  # ✅ Orange Active Menu
                    "box-shadow": "0px 0px 10px #ff9800",
                    "border-radius": "8px",
                    "font-weight": "bold",
                },
                "nav-icon": {
                    "color": "#f4d03f",  # ✅ Soft Yellow Icons
                    "font-size": "20px",
                },
            }
        )
        else:
            choice = option_menu(
                menu_title="🌟 Main Menu",
                options=["🏠 Home", "📝 Register", "🔑 Login", "ℹ️ About", "📞 Contact"],
                # icons=["house", "pencil", "key", "info", "phone"],
                menu_icon="menu",
                default_index=0,
                styles={
                    "container": {
                        "padding": "5px",
                       "background": "linear-gradient(to bottom, #00c6ff, #0072ff)",
                        "border-radius": "10px",
                        "box-shadow": "0px 0px 10px rgba(255, 255, 255, 0.2)",
                    },
                    "menu-title": {  
                        "font-size": "22px",
                        "font-weight": "bold",
                        "background": "#2d2d2d",
                        "color": "#ffffff",
                        "padding": "10px",
                        "border-radius": "8px",
                        "text-align": "center",
                    },
                    "nav-link": {
                        "font-size": "18px",
                        "text-align": "left",
                        "color": "#ffffff",
                        "padding": "10px",
                        "border-radius": "8px",
                        "transition": "all 0.3s ease-in-out",
                    },
                    "nav-link-hover": {
                        "background": "linear-gradient(to right, #ff512f, #dd2476)",
                        "color": "#ffffff",
                        "transform": "scale(1.05)",
                    },
                    "nav-link-selected": {
                        "background": "#4CAF50",
                        "box-shadow": "0px 0px 10px #4CAF50",
                        "border-radius": "8px",
                        "font-weight": "bold",
                    },
                    "nav-icon": {
                        "color": "#ffd700",
                        "font-size": "20px",
                    },
                }
            )


 
       





    DB_table_name = 'user_data'
    table_sql = """
        CREATE TABLE IF NOT EXISTS user_data (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Email_ID TEXT NOT NULL ,
            resume_score TEXT NOT NULL,
            Timestamp TEXT NOT NULL,
            Page_no TEXT NOT NULL,
            Predicted_Field TEXT NOT NULL,
            User_level TEXT NOT NULL,
            Actual_skills TEXT NOT NULL,
            Recommended_skills TEXT NOT NULL,
            Recommended_courses TEXT NOT NULL
        );
    """
    cursor.execute(table_sql)
    connection.commit()


    if choice == "🏠 Home":
        st.subheader("Welcome to Smart Resume Analyzer! 🎯")
        img = Image.open("./Logo/5052521.jpg")
        img = img.resize((400, 350))  # Resize if needed
        st.image(img)
        st.write("""
        🚀 This tool helps analyze resumes and provides recommendations based on skills.  
        🔍 It supports **normal users** (resume analysis) and **admin users** (data insights).  
        📂 Upload a resume and get insights instantly!  
        """)

        # Home Page Image
        # home_img = Image.open("./Logo/5052521.jpg")  # Ensure this image exists in your project folder
        # st.image(home_img, use_container_width=True)  # ✅ Updated parameter

    # ✅ Registration Section
    elif choice == "📝 Register":
        st.subheader("Register New Account 📝")
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if password == confirm_password:
                success = register_user(name, email, password)
                if success:
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error("Email already exists. Try a different one.")
            else:
                st.error("Passwords do not match!")

    elif choice == "🔑 Login":
        st.subheader("User Login 🔑")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            user = login_user(email, password)
            if user:
                # Store login details in session state
                st.session_state["logged_in"] = True
                st.session_state["user_name"] = user[1]  # Store Name
                st.session_state["user_email"] = user[2]  # Store Email
                
                st.success(f"Welcome, {user[1]}! Redirecting to Normal User Dashboard...")

                # Redirect to "Normal User" by setting session state and rerunning app
                st.session_state["redirect_to"] = "🏠 Home"
                st.rerun()  # Newer Streamlit versions use this
 
            else:
                st.error("Invalid email or password.")


    elif choice == '👤 Normal User' and st.session_state["logged_in"]:
        # st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>* Upload your resume, and get smart recommendation based on it."</h4>''',
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            
            # with st.spinner('Uploading your Resume....'):
            #     time.sleep(4)
            
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
                st.success("Hello " + resume_data['name'])
                st.subheader("**Your Basic info**")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are looking Fresher.</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',
                                unsafe_allow_html=True)

                st.subheader("**Skills Recommendation💡**")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')

                ##  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeplin', 'balsamiq', 'ui', 'prototyping', 'wireframes',
                                'storyframes', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeplin', 'Balsamiq',
                                              'Prototyping', 'Wireframes', 'Storyframes', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost🚀 the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas💡**")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration✍/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies⚽. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("**Resume Score📝**")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success('** Your Resume Writing Score: ' + str(score) + '**')
                st.warning(
                    "** Note: This score is calculated based on the content that you have added in your Resume. **")
                st.balloons()

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                            str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                            str(recommended_skills), str(rec_course))

                ## Resume writing video
                st.header("**Bonus Video for Resume Writing Tips💡**")
                resume_vid = random.choice(resume_videos)
                res_vid_title = fetch_yt_video(resume_vid)
                st.subheader("✅ **" + res_vid_title + "**")
                st.video(resume_vid)

                ## Interview Preparation Video
                st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
                interview_vid = random.choice(interview_videos)
                int_vid_title = fetch_yt_video(interview_vid)
                st.subheader("✅ **" + int_vid_title + "**")
                st.video(interview_vid)

                connection.commit()
            else:
                st.error('Something went wrong..')
    elif choice == "⚙️ Admin"and st.session_state["logged_in"]:
        ## Admin Side
        st.success('Welcome to Admin Side')
        # st.sidebar.subheader('**ID / Password Required!**')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'admin' and ad_password == 'root':
                st.success("Welcome Admin!")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                ## Pie chart for predicted field recommendations
                labels = plot_data.Predicted_Field.unique()
                print(labels)
                values = plot_data.Predicted_Field.value_counts()
                print(values)
                st.subheader("📈 **Pie-Chart for Predicted Field Recommendations**")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                ### Pie chart for User's👨‍💻 Experienced Level
                labels = plot_data.User_level.unique()
                values = plot_data.User_level.value_counts()
                st.subheader("📈 ** Pie-Chart for User's👨‍💻 Experienced Level**")
                fig = px.pie(df, values=values, names=labels, title="Pie-Chart📈 for User's👨‍💻 Experienced Level")
                st.plotly_chart(fig)


            else:
                st.error("Wrong ID & Password Provided")
    elif choice == "ℹ️ About":
        st.subheader("About Smart Resume Analyzer")
        st.write("""
        Smart Resume Analyzer is an AI-powered application that helps analyze resumes and provides recommendations 
        based on skills and job market trends. Our mission is to simplify the resume screening process and 
        enhance job seekers' chances of getting hired.
        
        ### Features:
        - 🚀 Resume Parsing & Skill Extraction  
        - 🔍 AI-Powered Job Recommendations  
        - 📊 Insights for Recruiters & HR  
        - 🎓 Course & Certification Suggestions  

        ### Technologies Used:
        - 🧠 Natural Language Processing (NLP)  
        - 🔥 Streamlit for Web UI  
        - 🗃️ SQLite Database  
        - 🏆 AI & Machine Learning Algorithms  
        """)

        # st.image("./Logo/SRA_Logo.jpg", use_column_width=True) 
        home_img = Image.open("./Logo/SRA_Logo.jpg")  # Ensure this image exists in your project folder
        st.image(home_img, use_container_width=True)  # Ensure this image exists in your project

    elif choice == "📞 Contact":
        st.subheader("Contact Us 📞")
        st.write("Have any questions or need support? Feel free to reach out to us!")

        # Contact Form
        contact_name = st.text_input("Your Name")
        contact_email = st.text_input("Your Email")
        contact_message = st.text_area("Your Message")

        if st.button("Send Message"):
            if contact_name and contact_email and contact_message:
                st.success("Thank you! Your message has been sent successfully. 📩")
            else:
                st.error("Please fill in all the fields before submitting.")

        # Additional Contact Information
        st.write("""
        **📍 Office Address:**  
        AI Solutions Pvt Ltd,  
        123 Tech Street, Bengaluru, India  
        
        **📧 Email:** support@smartresume.com  
        **📞 Phone:** +91 98765 43210  
        **🌐 Website:** [www.smartresume.com](https://www.smartresume.com)  
        """)

    elif choice == "🚪 Logout":
        # Clear user session
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        st.session_state["user_email"] = ""

        # ✅ Set redirect to Home after logout
        st.session_state["redirect_to"] = "🏠 Home"

        # Show success message
        st.success("You have logged out successfully. Redirecting to Home...")

        # ✅ Force rerun to apply changes
        st.rerun()



run()

