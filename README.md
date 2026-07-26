# FranchiseOps AI — Infosys Springboard Internship Project

An AI-powered franchise operations platform built as part of the Infosys Springboard internship program. The project is developed in milestones, with each milestone building on the previous one.

## About the Project

FranchiseOps AI is a Streamlit-based web application that helps a multi-outlet franchise business monitor and predict:
- **Workforce attrition** — which employees are likely to leave
- **Outlet performance** — which outlets are thriving vs. struggling
- **Inventory & supply chain risk** — which items are likely to run out of stock

It combines classic machine learning (scikit-learn models for prediction/classification) with a locally-hosted AI language model (Qwen-2.5-3B-Instruct) that acts as a chat-based copilot, explaining the agents' findings in plain language.

## Milestone Progress

### ✅ Milestone 1 — Secure Login System with OTP Verification
Built the foundational authentication system for the platform: user signup/login, password hashing, and a forgot-password flow secured with a one-time password (OTP) sent to the user's email for verification.

📁 See [`Milestone1/`](./Milestone1) for details.

### ✅ Milestone 2 — FranchiseOps AI Platform
Expanded on the Milestone 1 login system to build the full multi-agent platform: three ML-driven agents (Workforce, Outlets, Inventory), an AI chat copilot powered by a locally-hosted LLM, an admin dashboard, and a Streamlit front end — all hosted from Google Colab via ngrok.

📁 See [`Milestone2/`](./Milestone2) for the full README, notebook, and modular scripts.

## Tech Stack (overall)

- **Frontend:** Streamlit
- **Machine Learning:** scikit-learn (classification, regression, clustering)
- **AI/LLM:** Qwen-2.5-3B-Instruct (4-bit quantized, via `transformers` + `bitsandbytes`)
- **Auth & Security:** bcrypt, PyJWT, SMTP-based OTP email verification
- **Database:** SQLite
- **Hosting (dev/demo):** Google Colab + ngrok

## How to Run

Each milestone's notebook is self-contained and includes step-by-step setup instructions in its markdown cells (installing dependencies, configuring secrets, launching the app). Open the relevant milestone folder and start with its notebook and README.

## Author

Built as part of the Infosys Springboard Internship program.
