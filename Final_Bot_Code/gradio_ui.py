import gradio as gr
import os
import json
from main import run_chatbot  # expects (user_id, input_type, user_input)

PROFILE_PATH = "user_profiles.json"

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

# -------- Initialize Chat State --------
def init_state():
    return {
        "user_id": None,
        "name": None,
        "age": None,
        "chat_history": [],
    }

# -------- Chat Function --------
def chat_interface(user_message, state):
    state = state or init_state()
    if not user_message.strip():
        return state["chat_history"], state

    if not state["user_id"]:
        state["chat_history"].append({"role": "assistant", "content": "Please log in or create a profile first."})
        return state["chat_history"], state

    response = run_chatbot(state["user_id"], "text", user_message)
    state["chat_history"].append({"role": "user", "content": user_message})
    state["chat_history"].append({"role": "assistant", "content": response})

    return state["chat_history"], state

# -------- Profile Setup Logic --------
def set_returning_user(user_id):
    state = init_state()
    profile = load_user_profile(user_id)
    if not profile:
        raise gr.Error("User ID not found. Please register as a new user.")
    state["user_id"] = user_id
    state["name"] = profile["name"]
    state["age"] = profile["age"]
    return state

def set_new_user(name, age):
    state = init_state()
    if not name or not age:
        raise gr.Error("Name and age are required.")
    user_id = f"{name}_{age}"
    save_user_profile(user_id, name, age)
    state["user_id"] = user_id
    state["name"] = name
    state["age"] = age
    return state

# -------- Launch UI --------
def launch_app():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🩺 Emotion-Aware Healthcare Chatbot")

        with gr.Row():
            user_type = gr.Radio(
                ["Returning User", "New User"],
                label="Are you a returning user or a new user?",
                value="Returning User"
            )

        with gr.Group(visible=True) as returning_block:
            returning_id = gr.Textbox(label="Enter your User ID (e.g., name_age)")
            login_btn = gr.Button("Login")

        with gr.Group(visible=False) as new_user_block:
            name_input = gr.Textbox(label="Name")
            age_input = gr.Number(label="Age", precision=0)
            register_btn = gr.Button("Register")

        chat_output = gr.Chatbot(label="Conversation", height=450, type="messages")
        user_input = gr.Textbox(label="Your message", placeholder="Type something...")
        send_btn = gr.Button("Send")

        state = gr.State(init_state())

        # Toggle form visibility
        def toggle_blocks(selection):
            return (
                gr.update(visible=selection == "Returning User"),
                gr.update(visible=selection == "New User")
            )

        user_type.change(fn=toggle_blocks, inputs=user_type, outputs=[returning_block, new_user_block])
        login_btn.click(fn=set_returning_user, inputs=returning_id, outputs=state)
        register_btn.click(fn=set_new_user, inputs=[name_input, age_input], outputs=state)
        send_btn.click(fn=chat_interface, inputs=[user_input, state], outputs=[chat_output, state])

    demo.launch()

if __name__ == "__main__":
    launch_app()
