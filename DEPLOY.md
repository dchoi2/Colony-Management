# Putting the Colony Manager online (shared web link)

This guide turns the app into a website your whole lab opens in a browser —
one shared database, no installs on anyone's computer. We'll use **Render.com**
because it can read this project's `render.yaml` and set everything up for you.

You do this **once**. It takes about 10 minutes.

---

## What you'll end up with

- A link like `https://colony-manager-xxxx.onrender.com`
- A shared PostgreSQL database in the cloud (everyone sees the same live data)
- Automatic updates: whenever the code is improved on GitHub, the site updates

---

## Step-by-step

### 1. Make a Render account
- Go to **https://render.com** and click **Get Started**.
- Choose **Sign in with GitHub** and authorize it (this lets Render see your repo).

### 2. Create the app from this repo
- In the Render dashboard, click **New +** (top right) → **Blueprint**.
- Find and select your repository: **`colony-management`**.
- Render detects the `render.yaml` file and shows it will create:
  - a **PostgreSQL database** (`colony-db`)
  - a **web service** (`colony-manager`)
- Give the group a name if asked, then click **Apply** / **Create**.

### 3. Wait for it to build
- Render installs everything and starts the app (first build takes a few
  minutes). When the web service shows **"Live"**, it's ready.

### 4. Open your link
- Click the web service (`colony-manager`). Its URL is near the top, e.g.
  `https://colony-manager-xxxx.onrender.com`.
- Open it — that's your colony manager, live on the internet. Share that link
  with your lab. 🎉

---

## Good to know

- **Free tier sleeps.** On Render's free plan the site "spins down" after
  ~15 minutes of no use, so the *first* visit after a quiet period takes
  ~30–60 seconds to wake up. After that it's fast. Upgrading the web service
  to the cheapest paid plan (a few dollars/month) keeps it always-on.
- **Free database expiry.** Render's *free* PostgreSQL is time-limited (it
  expires after a set period). For data you care about long-term, upgrade the
  database to the smallest paid plan, or take regular backups (Render has a
  one-click backup/export). I can help you set this up.
- **Your data is now in the cloud database**, not the `colony.db` file. The
  local file is only used when you run the app on your own computer.
- **Security:** the app currently has no login — anyone with the link can view
  and edit. If you want password protection before sharing it widely, tell me
  and I'll add user logins.

---

## Moving your existing local data online (optional)

If you've already entered animals locally and want them on the website, that's
a one-time data transfer (export from the local SQLite file, import into the
cloud database). Ask me and I'll provide a small script and walk you through it.
