# 🩺 HealthBuddy AI

A Streamlit multimodal health-information assistant powered by Gemini, with
optional Twilio WhatsApp summaries.

## Features

- Text-based health questions
- Lab report image/PDF analysis
- Prescription image/PDF reading and organization
- Conversation memory using a Gemini chat session
- Safety-focused medical prompt
- WhatsApp summary through Twilio Content API
- Streamlit Community Cloud deployment

## 1. Create the environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Install packages:

```powershell
pip install -r requirements.txt
```

## 2. Configure secrets

Copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

Then add your real Gemini and Twilio credentials.

Never commit `secrets.toml`.

## 3. Run

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, normally:

```text
http://localhost:8501
```

## 4. Twilio WhatsApp setup

1. Create/sign in to Twilio.
2. Open the WhatsApp Sandbox.
3. Join the sandbox from the WhatsApp number you want to test.
4. Create an approved Content Template with two variables:
   - `{{1}}` = user's name
   - `{{2}}` = generated health summary
5. Put the resulting Content SID (`HX...`) in `TWILIO_CONTENT_SID`.

Example template:

```text
Hi {{1}}, here is your HealthBuddy summary:

{{2}}
```

## Safety

HealthBuddy is designed to explain and organize health information. It must
not be presented as a diagnostic or prescribing system. Users should consult
qualified healthcare professionals for medical decisions, and emergencies
require urgent professional care.
