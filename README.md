# APK Share - Short Direct Download Links

Upload APK files and get short direct download links. No account needed.

## Features

- Short links (6 characters, e.g., `https://domain.com/aB3xY9`)
- Direct download when clicking the link (no landing page)
- No account or registration required
- Mobile responsive
- QR code generation
- Upload progress with speed
- Max 200MB per file

## Local Development

```bash
npm install
npm start
```

Open http://localhost:3000

## Deployment

### Render (Recommended - Free)

1. Push code to GitHub
2. Go to render.com → New → Web Service
3. Connect your repo
4. Build Command: `npm install`
5. Start Command: `npm start`
6. Add Disk: Mount path `/app/uploads`, Size 1GB

### Railway (Free)

1. Push code to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Set start command: `npm start`

### Vercel (Serverless)

For Vercel, use the serverless function version in `vercel/` directory.

## How It Works

1. Upload APK file
2. Server generates a unique 6-character short ID
3. File is stored with UUID filename
4. Short link is returned (e.g., `https://domain.com/aB3xY9`)
5. When someone visits the short link, the file downloads automatically
