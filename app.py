import json

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="HealthBuddy AI",
    page_icon="🩺",
    layout="centered",
)


# ============================================================
# SECRETS / CONFIG
# ============================================================

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

TWILIO_ACCOUNT_SID = st.secrets.get(
    "TWILIO_ACCOUNT_SID", ""
)

TWILIO_AUTH_TOKEN = st.secrets.get(
    "TWILIO_AUTH_TOKEN", ""
)

TWILIO_WHATSAPP_FROM = st.secrets.get(
    "TWILIO_WHATSAPP_FROM",
    "whatsapp:+14155238886",
)

TWILIO_CONTENT_SID = st.secrets.get(
    "TWILIO_CONTENT_SID", ""
)

MODEL_NAME = st.secrets.get(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


# ============================================================
# CLIENTS
# ============================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(
        api_key=GEMINI_API_KEY
    )


@st.cache_resource
def get_twilio_client():
    return TwilioClient(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN,
    )


# ============================================================
# BASIC CHECK
# ============================================================

if not GEMINI_API_KEY:
    st.error(
        "Gemini API key is missing. "
        "Please add GEMINI_API_KEY to .streamlit/secrets.toml."
    )
    st.stop()


gemini_client = get_gemini_client()


# ============================================================
# SESSION STATE
# ============================================================

if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if "name" not in st.session_state:
    st.session_state.name = ""

if "whatsapp_number" not in st.session_state:
    st.session_state.whatsapp_number = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def twilio_ready():
    return all(
        [
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
            TWILIO_WHATSAPP_FROM,
            TWILIO_CONTENT_SID,
        ]
    )


def add_message(
    role,
    kind,
    content,
    label=None,
):
    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
            "label": label,
        }
    )


def display_message(message):

    with st.chat_message(
        message["role"],
        avatar="🩺" if message["role"] == "assistant" else "👤",
    ):

        if message["kind"] == "text":

            st.markdown(
                message["content"]
            )

        elif message["kind"] == "image":

            st.image(
                message["content"],
                width="stretch",
            )

            if message.get("label"):
                st.caption(
                    f"📎 {message['label']}"
                )


def ask_gemini(parts, multimodal=False):

    try:

        if multimodal:

            response = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=parts,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )

        else:

            response = st.session_state.chat.send_message(
                parts
            )

        if response.text:
            return response.text

        return "I couldn't generate a response."

    except Exception as error:

        return (
            "Sorry, I couldn't process that request right now.\n\n"
            f"Technical detail: {error}"
        )


def send_whatsapp(summary):

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return False, "Twilio Account SID or Auth Token is missing."

    if not st.session_state.whatsapp_number:
        return False, "WhatsApp number is missing."

    try:

        client = TwilioClient(
            TWILIO_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN,
        )

        to_number = st.session_state.whatsapp_number.strip()

        if not to_number.startswith("+"):
            to_number = "+" + to_number

        message = client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            body=summary,
        )

        return True, message.sid

    except Exception as error:

        return False, str(error)

# ============================================================
# ONBOARDING SCREEN
# ============================================================

if not st.session_state.onboarded:

    st.title("🩺 HealthBuddy AI")

    st.subheader(
        "Your AI health information assistant"
    )

    st.write(
        "Ask general health questions or upload "
        "lab reports, prescriptions, and medical documents "
        "for simple explanations."
    )

    st.divider()

    with st.form("onboarding"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name",
        )

        whatsapp = st.text_input(
            "WhatsApp number",
            placeholder="+91XXXXXXXXXX",
            help="Include your country code.",
        )

        submitted = st.form_submit_button(
            "🚀 Start HealthBuddy",
            width="stretch",
        )

    st.info(
        "🔒 HealthBuddy provides general health information "
        "and does not diagnose conditions or prescribe treatment."
    )

    if submitted:

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not whatsapp.strip():

            st.warning(
                "Please enter your WhatsApp number."
            )

        else:

            try:

                chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    ),
                )

                st.session_state.chat = chat

                st.session_state.name = (
                    name.strip()
                )

                st.session_state.whatsapp_number = (
                    whatsapp.strip()
                )

                st.session_state.messages = []

                st.session_state.onboarded = True

                welcome = WELCOME_MESSAGE_TEMPLATE.format(
                    name=st.session_state.name
                )

                add_message(
                    "assistant",
                    "text",
                    welcome,
                )

                st.rerun()

            except Exception as error:

                st.error(
                    "Unable to start HealthBuddy.\n\n"
                    f"Technical detail: {error}"
                )

    st.stop()


# ============================================================
# MAIN HEADER
# ============================================================

col1, col2 = st.columns(
    [4, 1]
)

with col1:

    st.title("🩺 HealthBuddy AI")

    st.caption(
        f"Welcome, {st.session_state.name} • "
        "General health information only"
    )

with col2:

    if st.button(
        "🔄 New Chat",
        width="stretch",
    ):

        try:

            st.session_state.chat = (
                gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    ),
                )
            )

            st.session_state.messages = []

            welcome = WELCOME_MESSAGE_TEMPLATE.format(
                name=st.session_state.name
            )

            add_message(
                "assistant",
                "text",
                welcome,
            )

            st.rerun()

        except Exception as error:

            st.error(
                f"Could not start a new chat: {error}"
            )


st.divider()


# ============================================================
# QUICK ACTIONS
# ============================================================

st.subheader("How can I help?")

col1, col2, col3 = st.columns(3)

with col1:

    st.info(
        "💬 **Ask a question**\n\n"
        "Ask general health questions "
        "in simple language."
    )

with col2:

    st.info(
        "📄 **Upload a report**\n\n"
        "Upload a lab report or medical document "
        "for explanation."
    )

with col3:

    st.info(
        "💊 **Upload a prescription**\n\n"
        "Help read and organize clearly visible "
        "prescription information."
    )


st.divider()


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    display_message(message)


# ============================================================
# CHAT INPUT
# ============================================================

user_input = st.chat_input(
    "Ask a health question or attach a report...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp",
        "pdf",
    ],
)


# ============================================================
# PROCESS INPUT
# ============================================================

if user_input:

    text = user_input.text.strip()

    uploaded_file = (
        user_input.files[0]
        if user_input.files
        else None
    )

    parts = []

    # --------------------------------------------------------
    # UPLOADED FILE
    # --------------------------------------------------------

    if uploaded_file is not None:

        file_bytes = uploaded_file.getvalue()

        file_name = (
            uploaded_file.name
            or "uploaded document"
        )

        mime_type = (
            uploaded_file.type
            or "application/octet-stream"
        )

        # IMAGE
        if mime_type.startswith("image/"):

            add_message(
                "user",
                "image",
                file_bytes,
                label=file_name,
            )

            parts.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                )
            )

        # PDF
        elif mime_type == "application/pdf":

            add_message(
                "user",
                "text",
                f"📄 Uploaded document: **{file_name}**",
            )

            parts.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type="application/pdf",
                )
            )

        else:

            st.error(
                "Please upload a JPG, JPEG, PNG, WEBP, "
                "or PDF file."
            )

            st.stop()


    # --------------------------------------------------------
    # USER TEXT
    # --------------------------------------------------------

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # --------------------------------------------------------
    # FILE WITHOUT TEXT
    # --------------------------------------------------------

    elif uploaded_file is not None:

        parts.append(
            """
            Analyze the uploaded document carefully.

            If it is a medical document, explain only
            the information that is clearly visible.

            If it is a laboratory report, identify:
            - test names
            - reported values
            - units
            - reference ranges
            - flags shown by the laboratory

            If it is a prescription, identify only clearly
            visible medicine names, strengths, and written
            instructions.

            If it is not a medical document, clearly explain
            what type of document it appears to be.

            Do not diagnose.
            Do not prescribe.
            Do not recommend changing medication.
            Do not invent unreadable information.
            """
        )


    # --------------------------------------------------------
    # SEND TO GEMINI
    # --------------------------------------------------------

    if parts:

        with st.spinner(
            "🩺 HealthBuddy is thinking..."
        ):

            answer = ask_gemini(
                parts,
                multimodal=(
                    uploaded_file is not None
                ),
            )

        add_message(
            "assistant",
            "text",
            answer,
        )

        st.rerun()


# ============================================================
# WHATSAPP SUMMARY
# ============================================================

st.divider()

col1, col2 = st.columns(
    [3, 1]
)

with col1:

    st.caption(
        "📲 Want a summary of this conversation?"
    )

with col2:

    if st.button(
        "Send to WhatsApp",
        width="stretch",
        disabled=(
            len(st.session_state.messages) < 2
        ),
    ):

        with st.spinner(
            "Preparing your summary..."
        ):

            summary = ask_gemini(
                [SUMMARY_REQUEST_PROMPT]
            )

            success, result = send_whatsapp(
                summary
            )

        if success:

            st.success(
                "Summary sent to WhatsApp! 📲"
            )

        else:

            st.error(
                f"Could not send WhatsApp message: {result}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🔒 HealthBuddy AI provides general health information only. "
    "It is not a doctor and does not provide diagnosis or treatment. "
    "For emergencies or serious symptoms, seek professional medical care."
)