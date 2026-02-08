# 🚀 Deployment Guide: AI Excel Cleaner with Supabase

This guide explains how to deploy the **AI Excel Cleaner** with the newly integrated **Supabase Authentication**.

## 1. Supabase Setup (Backend & Auth)

We use Supabase for handling user authentication (Login/Register).

1.  **Create a Project**: Go to [Supabase.com](https://supabase.com) and create a new project.
2.  **Get Credentials**:
    *   Go to **Project Settings** -> **API**.
    *   Copy the `Project URL` (SUPABASE_URL).
    *   Copy the `anon public` Key (SUPABASE_KEY).
3.  **Enable Auth**:
    *   Go to **Authentication** -> **Providers**.
    *   Ensure **Email** is enabled.
    *   (Optional) Disable "Confirm email" in **Authentication** -> **URL Configuration** if you want instant access for testing.

## 2. Deployment Options

### Option A: Render (Recommended for Streamlit)
We recommend **Render** because it natively supports Dockerized applications like Streamlit, which require a persistent server (unlike Vercel's serverless functions).

1.  **Push to GitHub**: Ensure your code is in a GitHub repository.
2.  **Create Web Service**:
    *   Go to [dashboard.render.com](https://dashboard.render.com).
    *   Click **New +** -> **Web Service**.
    *   Connect your GitHub repository.
3.  **Configuration**:
    *   **Runtime**: Select **Docker**.
    *   **Region**: Choose one close to you (e.g., Singapore/Oregon).
    *   **Free Tier**: Select "Free".
4.  **Environment Variables** (Crucial):
    *   Scroll down to "Environment Variables".
    *   Add `SUPABASE_URL`: (Paste from Supabase)
    *   Add `SUPABASE_KEY`: (Paste from Supabase)
5.  **Deploy**: Click "Create Web Service".

### Option B: Streamlit Cloud (Easiest)
1.  Go to [share.streamlit.io](https://share.streamlit.io).
2.  Connect GitHub repo.
3.  In "Advanced Settings", add the secrets:
    ```toml
    SUPABASE_URL = "..."
    SUPABASE_KEY = "..."
    ```
4.  Deploy.

### Why not Vercel?
Vercel is optimized for **Serverless** frameworks (Next.js, React). Streamlit requires a **continuous running server** (WebSocket connection) to maintain the app state. Deploying Streamlit on Vercel often leads to:
*   Timeouts during file processing.
*   "Connection lost" errors.
*   Cold start delays.
**Render** or **Streamlit Cloud** provides the dedicated server environment needed for a stable experience.

## 3. Local Development

To run locally with Auth:

1.  Set environment variables (PowerShell):
    ```powershell
    $env:SUPABASE_URL="your_url"
    $env:SUPABASE_KEY="your_key"
    streamlit run app.py
    ```
    
2.  Or create `.streamlit/secrets.toml`:
    ```toml
    SUPABASE_URL = "your_url"
    SUPABASE_KEY = "your_key"
    ```
