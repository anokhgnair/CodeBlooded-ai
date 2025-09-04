# =========================
# CodeBlooded AI — Tkinter Chat (Streamlit-y UI)
# =========================

# 🧱 import the building blocks
import google.generativeai as genai          # talk to Gemini
import json, os                               # save/load chat as a file
from datetime import datetime                 # put time on messages
import threading                              # stream reply without freezing UI
import customtkinter as ctk                   # GUI toolkit
from PIL import Image, ImageTk                # show a small logo
import google.api_core.exceptions             # catch API permission errors
import itertools                              # make "Typing..." bounce

# 🎨 Set the theme
ctk.set_default_color_theme("NightTrain.json")

# 💾 put the history file next to this .py (so we never “lose” it)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "CodeBlooded_AI_history.json")

# 🔑 read API key safely (don’t hardcode secrets)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set GOOGLE_API_KEY in your environment variables.")

# 🛰️ connect to Gemini
genai.configure(api_key=api_key)
# pick a fast, current model
model = genai.GenerativeModel("gemini-1.5-flash")

# 🧠 helper: load old messages from json
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # file broken? start fresh
    return []

# 🧠 helper: save new message pair to json
def save_message(user_msg, ai_msg):
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),  # when this happened
        "user": user_msg,                          # what you said
        "assistant": ai_msg                        # what bot said
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

# 🎨 UI constants
ASSISTANT_NAME = "CodeBlooded AI"
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 12
FONT_BOLD = (FONT_FAMILY, FONT_SIZE, "bold")
FONT_NORMAL = (FONT_FAMILY, FONT_SIZE)
# =========================
# Custom avatars & logos
# =========================
USER_AVATAR_PATH = r"C:\Users\Anokh G Nair\Desktop\ANOKHproject\aichatbot\useremoji.png"
AI_AVATAR_PATH   = r"C:\Users\Anokh G Nair\Desktop\ANOKHproject\aichatbot\ai2_logo.png"


# 🖼️ window: where we draw everything
root = ctk.CTk()
root.title(f"Chat with {ASSISTANT_NAME}")
root.geometry("700x800")

# 🏷️ header bar (logo + title + buttons)
header_frame = ctk.CTkFrame(root)
header_frame.pack(side=ctk.TOP, fill="x", padx=10, pady=10)

# --- Right side buttons ---
right_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
right_frame.pack(side="right", fill="y", padx=5)

def clear_chat():
    # remove all UI message widgets
    for w in scrollable_frame.winfo_children():
        w.destroy()
    # wipe file on disk
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4)

btn_clear = ctk.CTkButton(right_frame, text="🗑️", command=clear_chat, width=40)
btn_clear.pack(pady=5)

def toggle_theme():
    mode = ctk.get_appearance_mode()
    if mode == "Dark":
        ctk.set_appearance_mode("Light")
    else:
        ctk.set_appearance_mode("Dark")

btn_theme = ctk.CTkButton(right_frame, text="🌙", command=toggle_theme, width=40)
btn_theme.pack(pady=5)


# --- Center logo and title ---
center_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
center_frame.pack(expand=True, fill="both")

# 🖼️ logo (use your full path)
LOGO_PATH = r"./logoofcodebloodedaititle.png"
logo_photo = None
try:
    if os.path.exists(LOGO_PATH):
        logo_image = Image.open(LOGO_PATH).resize((40, 40), Image.Resampling.LANCZOS)
        logo_photo = ctk.CTkImage(light_image=logo_image, dark_image=logo_image, size=(40, 40))
        logo_label = ctk.CTkLabel(center_frame, image=logo_photo, text="")
        logo_label.pack(pady=(10,0))
    else:
        logo_label = ctk.CTkLabel(center_frame, text="⚡", font=(FONT_FAMILY, 22))
        logo_label.pack(pady=(10,0))
except Exception:
    logo_label = ctk.CTkLabel(center_frame, text="⚡", font=(FONT_FAMILY, 22))
    logo_label.pack(pady=(10,0))

# title + subtitle stacked vertically
title_label = ctk.CTkLabel(center_frame, text=ASSISTANT_NAME, font=(FONT_FAMILY, 20, "bold"))
title_label.pack()

subtitle = ctk.CTkLabel(center_frame, text="Your Virtual Web Companion!", font=(FONT_FAMILY, 11))
subtitle.pack()

## 📝 input bar (bottom)
input_frame = ctk.CTkFrame(root)
input_frame.pack(side=ctk.BOTTOM, fill="x", padx=10, pady=10)

entry = ctk.CTkEntry(input_frame, font=(FONT_FAMILY, 12), placeholder_text="Ask me anything...")
entry.pack(side="left", expand=True, fill="x", ipady=8, padx=(0, 10))

send_btn = ctk.CTkButton(input_frame, text="Send", font=FONT_BOLD)
send_btn.pack(side="right")

# 🗨️ chat area (scrollable)
scrollable_frame = ctk.CTkScrollableFrame(root)
scrollable_frame.pack(expand=True, fill="both", padx=10, pady=(10, 0))

# 🧮 keep references to message widgets for resizing
all_message_widgets = []

# ✨ helper: show one message bubble (user or assistant)
def display_message(role, message):
    # row: holds one bubble; lets us align left/right
    row_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")

    bubble_fg = "transparent" if role == "user" else "#374151"
    bubble = ctk.CTkFrame(row_frame, fg_color=bubble_fg)

    # avatar + name row
    name_frame = ctk.CTkFrame(bubble, fg_color="transparent")

    USER_AVATAR_PATH = r"./useremoji.png"
    AI_AVATAR_PATH   = r"./ai2_logo.png"

    if role == "user":
        # USER side
        try:
            if os.path.exists(USER_AVATAR_PATH):
                img = Image.open(USER_AVATAR_PATH).resize((45, 45), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(45, 45))
                avatar = ctk.CTkLabel(name_frame, image=photo, text="")
                avatar.image = photo
            else:
                avatar = ctk.CTkLabel(name_frame, text="🙂", font=(FONT_FAMILY, 25))
        except Exception:
            avatar = ctk.CTkLabel(name_frame, text="🙂", font=(FONT_FAMILY, 25))

        name = ctk.CTkLabel(name_frame, text="You", font=(FONT_FAMILY, FONT_SIZE + 1, "bold"))
        avatar.pack(side="right", padx=6)
        name.pack(side="right")

    else:
        try:
            if os.path.exists(AI_AVATAR_PATH):
                img = Image.open(AI_AVATAR_PATH).resize((45, 45), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(45, 45))
                avatar = ctk.CTkLabel(name_frame, image=photo, text="")
                avatar.image = photo
            else:
                avatar = ctk.CTkLabel(name_frame, text="⚡", font=(FONT_FAMILY, 25))
        except Exception:
            avatar = ctk.CTkLabel(name_frame, text="⚡", font=(FONT_FAMILY, 25))

        name = ctk.CTkLabel(name_frame, text=ASSISTANT_NAME, font=(FONT_FAMILY, FONT_SIZE + 1, "bold"))
        avatar.pack(side="left", padx=6)
        name.pack(side="left")

    name_frame.pack(anchor="w" if role=="assistant" else "e", pady=(6,0), padx=10)

    # message text with nice width
    wraplength = max(200, int(root.winfo_width() * 0.7))
    msg_widget = ctk.CTkLabel(bubble, text=message, font=FONT_NORMAL, wraplength=wraplength, justify="left")
    msg_widget.pack(anchor="w", padx=10, pady=(2, 4))
    all_message_widgets.append(msg_widget)

    # tiny timestamp
    time_label = ctk.CTkLabel(bubble, text=datetime.now().strftime("%H:%M"), font=(FONT_FAMILY, 8))
    time_label.pack(anchor="e" if role == "user" else "w", padx=10, pady=(0, 6))

    # align the whole row (user on right, bot on left)
    if role == "user":
        row_frame.pack(fill="x", padx=(60, 10), pady=6)
        bubble.pack(anchor="e")
    else:
        row_frame.pack(fill="x", padx=(10, 60), pady=6)
        bubble.pack(anchor="w")

    # keep scroll at bottom
    scrollable_frame._parent_canvas.yview_moveto(1.0)

    return msg_widget


# 💬 “Typing…” animation under the assistant bubble
def start_typing_animation(label_widget):
    cycle = itertools.cycle(["Typing.", "Typing..", "Typing..."])
    label_widget._typing = True
    def tick():
        if getattr(label_widget, "_typing", False):
            label_widget.configure(text=next(cycle))
            label_widget.after(400, tick)
    tick()

def stop_typing_animation(label_widget):
    label_widget._typing = False

# 🚀 send message without freezing UI; stream chunks
def send_message_async(event=None):
    user_msg = entry.get()
    if not user_msg.strip():
        return

    # show the user's bubble
    display_message("user", user_msg)
    entry.delete(0, ctk.END)

    # block input while bot is talking
    entry.configure(state="disabled")
    send_btn.configure(state="disabled")

    # make assistant placeholder bubble
    assistant_msg_widget = display_message("assistant", "…")

    # add a tiny typing label (under that bubble)
    typing_label = ctk.CTkLabel(assistant_msg_widget.master, text="", font=(FONT_FAMILY, 8))
    typing_label.pack(anchor="w", padx=10, pady=(0, 4))
    start_typing_animation(typing_label)

    def generate():
        try:
            # clear placeholder text before streaming
            assistant_msg_widget.configure(text="")
            root.update_idletasks()

            # ask Gemini to stream chunks back
            response = model.generate_content(user_msg, stream=True)

            full_response = []
            for chunk in response:
                # chunk.text may be empty sometimes
                if chunk.text:
                    full_response.append(chunk.text)
                    # append chunk to what's already shown
                    current = assistant_msg_widget.cget("text")
                    assistant_msg_widget.configure(text=current + chunk.text)

                    # keep scrolled to bottom as we stream
                    scrollable_frame._parent_canvas.yview_moveto(1.0)
                    root.update_idletasks()

            # join all parts into one final message
            ai_msg = "".join(full_response).strip()
            if not ai_msg:
                ai_msg = "[No response from model]"
                assistant_msg_widget.configure(text=ai_msg)

            # turn “Typing…” into a final timestamp
            stop_typing_animation(typing_label)
            typing_label.configure(text=datetime.now().strftime("%H:%M"))

            # save both sides to history file
            save_message(user_msg, ai_msg)

        except google.api_core.exceptions.PermissionDenied as e:
            # common: bad key / wrong project / API disabled
            stop_typing_animation(typing_label)
            error_message = ("Authentication Error: Your API key is invalid, expired, or the Generative AI API "
                             "is not enabled for this project. Check GOOGLE_API_KEY and billing, then restart.")
            print(f"[API Permission Error] {e}")
            assistant_msg_widget.configure(text=error_message)
            typing_label.configure(text=datetime.now().strftime("%H:%M"))
            save_message(user_msg, error_message)

        except Exception as e:
            # any other surprise
            stop_typing_animation(typing_label)
            error_message = f"An unexpected error occurred: {e}"
            print(f"[Runtime Error] {e}")
            assistant_msg_widget.configure(text=error_message)
            typing_label.configure(text=datetime.now().strftime("%H:%M"))
            save_message(user_msg, error_message)

        finally:
            # let you type again
            entry.configure(state="normal")
            send_btn.configure(state="normal")
            entry.focus_set()
            scrollable_frame._parent_canvas.yview_moveto(1.0)
            root.update_idletasks()

    # run the network call in another thread (so UI stays smooth)
    threading.Thread(target=generate, daemon=True).start()

# 🖱️ click send
send_btn.configure(command=send_message_async)
# ⏎ press Enter to send
entry.bind("<Return>", send_message_async)

# ⌨️ shortcuts: Ctrl+L = clear, Ctrl+Enter = send
root.bind("<Control-l>", lambda e: clear_chat())
root.bind("<Control-Return>", send_message_async)

# 📜 redraw old messages on startup
for chat in load_history():
    display_message("user", chat["user"])
    display_message("assistant", chat["assistant"])

# 🧊 keep a reference to logo so it doesn’t disappear
if logo_photo:
    logo_label.image = logo_photo

# 🟢 go!
root.mainloop()