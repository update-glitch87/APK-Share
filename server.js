const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;
const UPLOAD_DIR = path.join(__dirname, 'uploads');
const DB_FILE = path.join(__dirname, 'db.json');
const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB

if (!fs.existsSync(UPLOAD_DIR)) {
    fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

let db = {};
if (fs.existsSync(DB_FILE)) {
    db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
}

function saveDb() {
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

function generateShortId() {
    const alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
        result += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    return result;
}

app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    next();
});

app.use(cors());
app.use(express.static('public'));

const storage = multer.diskStorage({
    destination: (req, file, cb) => cb(null, UPLOAD_DIR),
    filename: (req, file, cb) => {
        const uniqueId = crypto.randomUUID();
        const ext = path.extname(file.originalname).toLowerCase() || '.apk';
        cb(null, `${uniqueId}${ext}`);
    }
});

const upload = multer({
    storage,
    limits: { fileSize: MAX_FILE_SIZE },
    fileFilter: (req, file, cb) => {
        const allowedExts = ['.apk', '.apks', '.xapk', '.apkm'];
        const ext = path.extname(file.originalname).toLowerCase();
        if (allowedExts.includes(ext) || file.mimetype === 'application/vnd.android.package-archive') {
            cb(null, true);
        } else {
            cb(new Error('Only APK files allowed (.apk, .apks, .xapk, .apkm)'));
        }
    }
});

app.post('/api/upload', upload.single('apk'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    let shortId;
    do {
        shortId = generateShortId();
    } while (db[shortId]);

    db[shortId] = {
        originalName: req.file.originalname,
        fileName: req.file.filename,
        filePath: req.file.path,
        fileSize: req.file.size,
        uploadDate: new Date().toISOString()
    };

    saveDb();

    const protocol = req.headers['x-forwarded-proto'] || req.protocol;
    const shortUrl = `${protocol}://${req.get('host')}/${shortId}`;

    res.json({
        success: true,
        shortId,
        shortUrl,
        fileName: req.file.originalname,
        fileSize: req.file.size
    });
});

app.get('/:shortId', (req, res) => {
    const { shortId } = req.params;

    if (shortId === 'api' || shortId === 'uploads') {
        return res.status(404).send('Not found');
    }

    const file = db[shortId];

    if (!file) {
        return res.status(404).send('File not found or link expired');
    }

    if (!fs.existsSync(file.filePath)) {
        return res.status(404).send('File not found on server');
    }

    res.setHeader('Content-Disposition', `attachment; filename="${file.originalName}"`);
    res.setHeader('Content-Type', 'application/vnd.android.package-archive');
    res.download(file.filePath, file.originalName);
});

app.use((err, req, res, next) => {
    if (err instanceof multer.MulterError) {
        if (err.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'File too large. Max 200MB.' });
        }
        return res.status(400).json({ error: err.message });
    }
    if (err) {
        return res.status(400).json({ error: err.message });
    }
    next();
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`APK Share running on port ${PORT}`);
});
