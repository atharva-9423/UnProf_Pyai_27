<div align="center">

# 🔐 Day 27 — Environment & Security
### Preparing for Safe, Secure Deployment

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![python-dotenv](https://img.shields.io/badge/python--dotenv-.env%20Loader-yellow?style=for-the-badge)](https://pypi.org/project/python-dotenv/)
[![Security](https://img.shields.io/badge/Security-API%20Key%20Protected-green?style=for-the-badge&logo=shield&logoColor=white)]()

*Protecting secrets, organizing the project, and making it deployment-ready.*

</div>

---

## 📖 Overview

Day 27 is all about **security and professional project hygiene**. A real-world application should **never** have API keys or passwords hardcoded in the code or typed into the terminal each time. This day upgrades our app to use a `.env` file and `python-dotenv`, the industry-standard way to manage secrets.

## ✨ Key Changes

- **`.env` file:** A local file where you store your secrets (like `GEMINI_API_KEY`). This file lives only on **your machine**.
- **`python-dotenv`:** A library that automatically reads the `.env` file and injects the values into `os.environ` when the app starts — no manual `$env:` commands needed!
- **`.gitignore`:** A file that tells Git to **permanently ignore** your `.env` file so it is never accidentally committed and pushed to GitHub.
- **`.env.example`:** A safe template file (with no real secrets) committed to GitHub so teammates know what variables are needed.

## 📁 Project Structure

```text
UnProf_Pyai_27/
├── app.py               # Streamlit app (upgraded with dotenv)
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── .env                 # ⛔ YOUR REAL SECRETS (never commit!)
├── .env.example         # ✅ Safe template (committed to GitHub)
├── .gitignore           # Tells Git to ignore .env
└── documents/
    └── sample_notes.txt # Default knowledge base
```

## 🚀 Setup & Usage

### 1. Install Dependencies
```bash
pip install -U -r requirements.txt
```

### 2. Configure your `.env` file
Open the [`.env`](.env) file and replace the placeholder with your real key:
```env
GEMINI_API_KEY=AIza...your_real_key_here
```
> ⚠️ This is the ONLY place you need to put your API key. No more typing `$env:GEMINI_API_KEY` every time!

### 3. Run the Application
```bash
streamlit run app.py
```
The app will automatically read your `.env` file on startup!

---

## 🔐 Security Rules (Important!)

| Rule | Why |
|------|-----|
| ✅ Add `.env` to `.gitignore` | Prevents accidental key leaks on GitHub |
| ✅ Commit `.env.example` only | Shows teammates what variables are needed |
| ❌ Never hardcode keys in Python files | Anyone who reads your code can steal your quota |
| ❌ Never share your `.env` file | Treat it like a password |

---
<div align="center">
<i>Built for the 100 Days of Code challenge. Phase 4 - UI & Deployment.</i>
</div>
