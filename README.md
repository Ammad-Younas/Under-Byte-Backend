# Under Byte Backend

This is a FastAPI backend for the Under Byte Android application.

## Vercel Deployment

This project is configured for deployment on [Vercel](https://vercel.com).

### Prerequisites
1.  A Vercel account.
2.  Verify `vercel.json` exists in this directory.
3.  Verify `requirements.txt` is present.

### How to Deploy
1.  Install Vercel CLI: `npm i -g vercel`
2.  Run `vercel` in this directory.
3.  Follow the prompts.

### ⚠️ IMPORTANT: Database Persistence
This backend uses **SQLite** (`database.db`).