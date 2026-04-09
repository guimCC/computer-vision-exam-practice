# Visio Exam Practice App

Deploy-only package for the mobile-friendly Streamlit version of the exam study tool.

## What is included

- `app.py`: the Streamlit app
- `question_bank.json`: the generated bank used at runtime
- `build_report.json`: extraction/build summary
- `assets/problem_images/`: extracted problem images
- `.streamlit/config.toml`: default theme config for hosted deployment
- `requirements.txt`: runtime dependencies for hosting

This folder intentionally does **not** include the raw `exams/` source material or the local progress database.

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## GitHub + Streamlit Community Cloud

Recommended target account: `guimCC`

### 1. Create a new GitHub repository

Create a new repository under your personal account, for example:

- `visio-exam-practice`

Use a **private** repo unless you explicitly want the question bank public.

### 2. Push this folder

From inside this folder:

```bash
git init
git add .
git commit -m "Initial deployable study app"
git branch -M main
git remote add origin git@github.com:guimCC/visio-exam-practice.git
git push -u origin main
```

If you prefer HTTPS:

```bash
git remote add origin https://github.com/guimCC/visio-exam-practice.git
git push -u origin main
```

### 3. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Connect your GitHub account if needed
3. Select the repository
4. Branch: `main`
5. Main file path: `app.py`
6. Deploy

After that you will get a hosted URL you can open from your phone.

## Important note about progress

The app stores progress in `progress.sqlite3`.

On hosted Streamlit this is acceptable for a lightweight personal setup, but you should treat it as best-effort state, not guaranteed durable storage. If you want robust long-term mobile progress, the next improvement would be moving progress to a hosted database or browser-local persistence.
