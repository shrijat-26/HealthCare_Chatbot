import gradio as gr
import os
import json
import sounddevice as sd
from main import run_chatbot
from profile_manager import log_conditions

PROFILE_PATH = "user_profiles.json"

# ---------- Load & Save Profile ----------
def load_user_profile(user_id):
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f).get(user_id, None)
    return None

def save_user_profile(user_id, name, age):
    data = {}
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            data = json.load(f)
    data[user_id] = {"name": name, "age": age, "conditions": []}
    with open(PROFILE_PATH, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Voice Input Handler ----------
def record_audio(duration=5, sr=16000):
    audio = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten(), sr

# ---------- State Init ----------
def init_state():
    return {"user_id": None, "name": None, "age": None, "chat_history": []}

# ---------- Chat Interface ----------
def chat_interface(user_message, state):
    state = state or init_state()
    if not user_message.strip():
        return state["chat_history"], state

    if not state["user_id"]:
        state["chat_history"].append({"role": "assistant", "content": "Please log in or register first."})
        return state["chat_history"], state

    response = run_chatbot(state["user_id"], "text", user_message)
    log_conditions(state["user_id"], user_message)
    state["chat_history"].append({"role": "user", "content": user_message})
    state["chat_history"].append({"role": "assistant", "content": response})
    return state["chat_history"], state

# ---------- Voice Interface ----------
def voice_chat(state):
    state = state or init_state()
    if not state["user_id"]:
        return state["chat_history"], state

    audio, sr = record_audio()
    bot_response, transcript = run_chatbot(state["user_id"], "audio", (audio, sr))
    log_conditions(state["user_id"], transcript)
    state["chat_history"].append({"role": "user", "content": f"[Voice Input] {transcript}"})
    state["chat_history"].append({"role": "assistant", "content": bot_response})
    return state["chat_history"], state

# ---------- Profile Setup ----------
def set_returning_user(user_id):
    state = init_state()
    profile = load_user_profile(user_id)
    if not profile:
        raise gr.Error("User ID not found. Register as a new user.")
    state.update({"user_id": user_id, "name": profile["name"], "age": profile["age"]})
    return state

def set_new_user(name, age):
    state = init_state()
    if not name or not age:
        raise gr.Error("Name and age required.")
    user_id = f"{name}_{age}"
    save_user_profile(user_id, name, age)
    state.update({"user_id": user_id, "name": name, "age": age})
    return state

# ---------- Dashboard for Conditions ----------
def view_conditions(state):
    if not state or not state.get("user_id"):
        return "Please log in first."
    profile = load_user_profile(state["user_id"])
    if not profile:
        return "Profile not found."
    if not profile.get("conditions"):
        return "No conditions detected yet."
    logs = profile["conditions"]
    return "\n".join([f"{entry['timestamp']} - {entry['condition']}" for entry in logs])

# ---------- Launch App ----------
def launch_app():
    with gr.Blocks(theme=gr.themes.Soft(), css="""
        .gradio-container {
            font-family: 'Inter', sans-serif;
            max-width: 900px;
            margin: auto;
        }
        .gr-box {
            border-radius: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            padding: 2rem;
        }
        .gr-button {
            border-radius: 0.75rem;
            padding: 0.6rem 1.2rem;
            font-size: 1rem;
        }
        .gr-chatbot {
            background: #f9f9f9;
            border-radius: 1rem;
            padding: 1rem;
        }
    """) as demo:
        gr.Markdown("""
        <h1 style='text-align: center;'>🩺 Emotion-Aware Healthcare Chatbot</h1>
        <p style='text-align: center;'>Speak or type to receive empathetic and intelligent support.</p>
        """)

        with gr.Row():
            user_type = gr.Radio(["Returning User", "New User"], label="User Type", value="Returning User")

        with gr.Group(visible=True) as returning_block:
            returning_id = gr.Textbox(label="User ID (e.g., name_age)")
            login_btn = gr.Button("Login")

        with gr.Group(visible=False) as new_user_block:
            name_input = gr.Textbox(label="Name")
            age_input = gr.Number(label="Age", precision=0)
            register_btn = gr.Button("Register")

        chat_output = gr.Chatbot(label="Conversation", height=450, type="messages")
        user_input = gr.Textbox(label="Your message", placeholder="Type something...", lines=1)
        with gr.Row():
            send_btn = gr.Button("Send", variant="primary")
            voice_btn = gr.Button("🎙️ Speak")

        view_cond_btn = gr.Button("📋 View Health Log")
        conditions_output = gr.Textbox(label="Condition Log", lines=6, interactive=False)

        state = gr.State(init_state())

        user_type.change(lambda t: (gr.update(visible=t == "Returning User"), gr.update(visible=t == "New User")), inputs=user_type, outputs=[returning_block, new_user_block])
        login_btn.click(fn=set_returning_user, inputs=returning_id, outputs=state)
        register_btn.click(fn=set_new_user, inputs=[name_input, age_input], outputs=state)
        send_btn.click(fn=chat_interface, inputs=[user_input, state], outputs=[chat_output, state])
        voice_btn.click(fn=voice_chat, inputs=state, outputs=[chat_output, state])
        view_cond_btn.click(fn=view_conditions, inputs=state, outputs=conditions_output)

    demo.launch()

if __name__ == "__main__":
    launch_app()
