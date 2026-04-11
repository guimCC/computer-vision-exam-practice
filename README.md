# Computer Vision Exam Practice

Mobile-friendly Streamlit app for practicing a deduplicated computer vision exam bank built from past exams and optional online quizzes.

## What the app does

- Multiple-choice practice with topic-based entry points
- Per-user progress, bookmarks, failed-question tracking, and frozen MCQ sessions
- Open-ended problem study with show/hide stored answers and extracted images
- Question browser with filters by topic, source, year, and progress state
- One-tap copy icon for exporting question text and answers into another LLM

The hosted app is designed for phone use first, but it also works on desktop.

## What is in this repo

- `app.py`: Streamlit application
- `question_bank.json`: generated canonical question bank used at runtime
- `build_report.json`: extraction summary for the generated bank
- `assets/problem_images/`: extracted images linked to some open-ended problems
- `.streamlit/config.toml`: default Streamlit theme config
- `requirements.txt`: runtime dependencies

This repo intentionally does not include the raw source material used to build the bank.

## Current study model

### Multiple choice

- Practice starts from a topic chooser instead of dropping directly into a question
- `Unseen only` creates a frozen session queue, so answered questions do not disappear mid-review
- Answer review shows:
  - all options
  - your selected answer
  - the correct answer
  - explanation when available
- Active sessions resume after reloads or weak connections

### Problems

- Problems are separate from MCQ
- Stored answers can be shown or hidden while studying
- Confidence can be marked per problem
- Extracted images are rendered inline when available

## How progress works

- If authentication is enabled, progress is stored per signed-in user
- The same user can continue on laptop and phone with the same progress
- Classmates do not share progress with each other if they log in with different accounts
- Progress is stored in `progress.sqlite3` on the Streamlit host

This is intentionally lightweight. It avoids a hosted database, but it should be treated as best-effort state rather than guaranteed durable storage.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub
2. Open [share.streamlit.io](https://share.streamlit.io/)
3. Select:
   - repository: this repo
   - branch: `main`
   - entrypoint: `app.py`
4. Deploy

After deployment, Streamlit gives you a hosted URL that you can open from your phone.

## Enable login so progress is private per user

The app supports Streamlit authentication with Google OIDC.

References:

- [Streamlit authentication docs](https://docs.streamlit.io/develop/concepts/connections/authentication)
- [st.login / st.logout / st.user](https://docs.streamlit.io/develop/api-reference/user)

### 1. Create a Google OAuth client

In Google Cloud:

- create an OAuth client of type `Web application`
- add this authorized redirect URI:

```text
https://YOUR-APP-URL.streamlit.app/oauth2callback
```

### 2. Add Streamlit secrets

In Streamlit Community Cloud, open the app settings and paste secrets using this shape:

```toml
[auth]
redirect_uri = "https://YOUR-APP-URL.streamlit.app/oauth2callback"
cookie_secret = "replace-with-a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

There is a local template at `.streamlit/secrets.example.toml`.

### 3. Redeploy

After saving secrets, reboot or redeploy the app.

Expected behavior:

- same Google account on laptop and phone -> same progress
- different Google accounts -> separate progress
- no auth configured -> fallback guest mode

## Known limitations

- Progress is server-side SQLite, not a fully durable hosted database
- There is no offline mode or background sync
- Rebuilding the question bank is not part of this repo; this repo is runtime-only

## Runtime files you should not commit

- `.streamlit/secrets.toml`
- `progress.sqlite3`
- `__pycache__/`

## If you need to rebuild the bank

This deploy repo is runtime-only. Use the local builder project in:

- [study_tool](/Users/guimcc/Library/Mobile%20Documents/com~apple~CloudDocs/MatCad/4t/Visió/study_tool)

That folder contains:

- `build_bank.py`
- the original local README for extraction/rebuild flow
- the local copy of the app
