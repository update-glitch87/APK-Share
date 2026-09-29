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
const MAX_DISK_USAGE = 400 * 1024 * 1024; // 400MB limit

const ADMIN_USER = 'sialkwl';
const ADMIN_PASS = 'Sialkwl@9900';

// In-memory token store
const adminTokens = new Set();

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

function getDirSize(dir) {
    let size = 0;
    try {
        const files = fs.readdirSync(dir);
        for (const file of files) {
            const filePath = path.join(dir, file);
            const stats = fs.statSync(filePath);
            if (stats.isFile()) size += stats.size;
        }
    } catch (err) {
        console.error('Error calculating dir size:', err);
    }
    return size;
}

function cleanupOldFiles() {
    let currentSize = getDirSize(UPLOAD_DIR);
    if (currentSize <= MAX_DISK_USAGE) return;

    console.log(`Disk usage ${currentSize} exceeds limit ${MAX_DISK_USAGE} — cleaning up...`);

    const files = Object.entries(db)
        .map(([shortId, data]) => ({ shortId, ...data }))
        .sort((a, b) => new Date(a.uploadDate) - new Date(b.uploadDate));

    for (const file of files) {
        if (currentSize <= MAX_DISK_USAGE * 0.8) break;

        if (fs.existsSync(file.filePath)) {
            const fileSize = fs.statSync(file.filePath).size;
            fs.unlinkSync(file.filePath);
            currentSize -= fileSize;
            console.log(`Deleted old file: ${file.originalName}`);
        }
        delete db[file.shortId];
    }

    saveDb();
    console.log('Cleanup complete');
}

setInterval(cleanupOldFiles, 5 * 60 * 1000);

app.use((req, res, next) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    next();
});

app.use(cors());
app.use(express.json());
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

function requireAdmin(req, res, next) {
    const token = req.headers['x-admin-token'];
    if (token && adminTokens.has(token)) {
        next();
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
}

app.post('/api/admin/login', (req, res) => {
    const { username, password } = req.body;
    if (username === ADMIN_USER && password === ADMIN_PASS) {
        const token = crypto.randomBytes(32).toString('hex');
        adminTokens.add(token);
        res.json({ success: true, token });
    } else {
        res.status(401).json({ error: 'Invalid credentials' });
    }
});

app.post('/api/admin/logout', (req, res) => {
    const token = req.headers['x-admin-token'];
    if (token) adminTokens.delete(token);
    res.json({ success: true });
});

app.get('/api/admin/files', requireAdmin, (req, res) => {
    const files = Object.entries(db).map(([shortId, data]) => ({
        shortId,
        ...data
    }));
    res.json({ files });
});

app.delete('/api/admin/delete/:shortId', requireAdmin, (req, res) => {
    const { shortId } = req.params;
    const file = db[shortId];

    if (!file) {
        return res.status(404).json({ error: 'File not found' });
    }

    if (fs.existsSync(file.filePath)) {
        fs.unlinkSync(file.filePath);
    }

    delete db[shortId];
    saveDb();

    res.json({ success: true, message: 'File deleted' });
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
    cleanupOldFiles();

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
