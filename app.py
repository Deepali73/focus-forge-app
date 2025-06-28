import streamlit as st
import json, time, os
import hashlib
import cv2
import numpy as np
import random
from cvzone.FaceMeshModule import FaceMeshDetector
from streamlit.components.v1 import html

# --- File to store user data ---
USER_DATA_FILE = "users.json"

# --- Initialize user data file if missing ---
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({}, f)

# --- Helper Functions ---
def load_users():
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    users = load_users()
    return username in users and users[username]["password"] == hash_password(password)

def register_user(username, password, name, age):
    users = load_users()
    if username in users:
        return False
    users[username] = {
        "name": name,
        "age": age,
        "password": hash_password(password),
        "sleep_incidents": 0,
        "total_sleep_time": 0.0,
        "to_do_list": [],
        "timer": 0.0
    }
    save_users(users)
    return True

def get_user_data(username):
    user = load_users().get(username, {})
    user.setdefault("timer", 0.0)
    user.setdefault("sleep_incidents", 0)
    user.setdefault("total_sleep_time", 0.0)
    user.setdefault("to_do_list", [])
    return user

def update_user_data(username, field, value):
    users = load_users()
    if username in users:
        users[username][field] = value
        save_users(users)

# --- Motivational Phrases ---
phrases = [
    "Utho bhai! Neend me padhna mana hai.",
    "Zyada mat socho, bas padho!",
    "Focus karo! Aankhein khol lo.",
    "Padhai se bhaag mat yaar!",
    "Arey! Neend ko maaro goli, chalo padho."
]

# --- Streamlit Config ---
st.set_page_config(":brain: FocusForge: Study Wake App", layout="wide")

# --- Session State ---
for key in ["logged_in", "username", "monitoring", "eye_closed_start", "alerted", "start_time", "timer"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else None if key in ["username", "eye_closed_start", "start_time"] else 0.0 if key == "timer" else False

# --- Alarm with autoplay and loop for 20s ---
def play_alert():
    st.warning(random.choice(phrases))
    st.components.v1.html("""
    <audio id="alarm" autoplay>
        <source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg" type="audio/ogg">
        <source src="https://actions.google.com/sounds/v1/alarms/alarm_clock.mp3" type="audio/mpeg">
        Your browser does not support the audio tag.
    </audio>
    <script>
        const alarm = document.getElementById("alarm");
        let interval = setInterval(() => {
            alarm.play();
        }, 2000);

        setTimeout(() => {
            clearInterval(interval);
            alarm.pause();
            alarm.currentTime = 0;
        }, 20000);
    </script>
    """, height=0)




# --- Login UI ---
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 100px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='login-container'>
        <h1 style='color:#4CAF50;'>🧠 FocusForge: Study Wake App</h1>
        <h3 style='text-align:center;'>🔐 Login or Sign Up</h3>
    </div>
    """, unsafe_allow_html=True)

    action = st.radio("Action", ["Login", "Sign Up"], horizontal=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if action == "Login":
        if st.button("🔓 Login"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
        name = st.text_input("Full Name")
        age = st.text_input("Age")
        if st.button("📝 Register"):
            if not name or not age:
                st.warning("Please fill all fields")
            elif register_user(username, password, name, age):
                st.success("Registration successful. Please login.")
            else:
                st.warning("Username already exists")

else:
    user_info = get_user_data(st.session_state.username)
    st.sidebar.title(f"👋 Welcome {user_info.get('name')}!")
    st.sidebar.write(f"🧑 Age: {user_info.get('age')}")

    st.sidebar.subheader("📋 To-Do List")
    new_task = st.sidebar.text_input("Add a new task")
    if st.sidebar.button("➕ Add Task"):
        user_info["to_do_list"].append(new_task)
        update_user_data(st.session_state.username, "to_do_list", user_info["to_do_list"])
    for i, task in enumerate(user_info["to_do_list"]):
        if st.sidebar.checkbox(task, key=f"task_{i}"):
            user_info["to_do_list"].pop(i)
            update_user_data(st.session_state.username, "to_do_list", user_info["to_do_list"])
            st.experimental_rerun()

    st.sidebar.subheader("⏱ Total Focus Timer")
    st.sidebar.write(f"📈 Focused Time: **{round(user_info.get('timer', 0.0), 2)} sec**")

    st.sidebar.subheader("😴 Sleep Stats")
    st.sidebar.write(f"🛌 Times Slept: {user_info.get('sleep_incidents', 0)}")
    st.sidebar.write(f"🕒 Sleep Duration: {round(user_info.get('total_sleep_time', 0.0), 2)} sec")

    st.title("🧠 FocusForge: Study Wake App")
    col_control, col_display = st.columns([1, 2])

    if col_control.button("✅ Start Monitoring"):
        st.session_state.monitoring = True
        st.session_state.eye_closed_start = None
        st.session_state.alerted = False
        st.session_state.start_time = time.time()

    if col_control.button("⛔ Stop Monitoring"):
        st.session_state.monitoring = False
        if st.session_state.start_time:
            duration = time.time() - st.session_state.start_time
            user_info["timer"] = user_info.get("timer", 0.0) + duration
            update_user_data(st.session_state.username, "timer", user_info["timer"])
            st.success(f"✅ Monitoring stopped. Session Focused Time: {round(duration, 2)} sec")

    if st.session_state.monitoring:
        detector = FaceMeshDetector(maxFaces=1)
        cap = cv2.VideoCapture(0)
        time.sleep(1)
        status = col_control.empty()
        frame_placeholder = col_display.empty()

        while st.session_state.monitoring:
            ret, frame = cap.read()
            if not ret:
                status.error("⚠️ Cannot access webcam.")
                break

            frame = cv2.flip(frame, 1)
            frame, faces = detector.findFaceMesh(frame, draw=False)

            if faces:
                face = faces[0]
                pairs = [(159, 145), (386, 374)]
                distances = [
                    np.linalg.norm(np.array(face[t]) - np.array(face[b]))
                    for t, b in pairs
                ]
                eye_dist = np.linalg.norm(np.array(face[33]) - np.array(face[263]))
                openness = np.mean(distances) / eye_dist

                now = time.time()
                if openness < 0.20:
                    if st.session_state.eye_closed_start is None:
                        st.session_state.eye_closed_start = now
                    elif (now - st.session_state.eye_closed_start) > 5:
                        if not st.session_state.alerted:
                            play_alert()
                            user_info = get_user_data(st.session_state.username)
                            user_info["sleep_incidents"] += 1
                            user_info["total_sleep_time"] += now - st.session_state.eye_closed_start
                            update_user_data(st.session_state.username, "sleep_incidents", user_info["sleep_incidents"])
                            update_user_data(st.session_state.username, "total_sleep_time", user_info["total_sleep_time"])
                            st.session_state.alerted = True
                else:
                    st.session_state.eye_closed_start = None
                    st.session_state.alerted = False

            frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        cap.release()
        frame_placeholder.empty()
        status.info("🔴 Monitoring stopped.")
