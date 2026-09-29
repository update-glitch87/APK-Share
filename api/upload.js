const { Router } = require('it-router');
const busboy = require('busboy');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs');
const path = require('path');

const UPLOAD_DIR = '/tmp/uploads';
const DB_FILE = '/tmp/db.json';

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

module.exports = async (req, res) => {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const bb = busboy({ headers: req.headers });
    const fields = {};
    let fileData = null;
    let fileName = '';

    bb.on('file', (name, file, info) => {
        fileName = info.filename;
        const chunks = [];
        file.on('data', (data) => chunks.push(data));
        file.on('end', () => {
            fileData = Buffer.concat(chunks);
        });
    });

    bb.on('field', (name, val) => {
        fields[name] = val;
    });

    bb.on('close', () => {
        if (!fileData) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        const ext = path.extname(fileName).toLowerCase();
        const allowedExts = ['.apk', '.apks', '.xapk', '.apkm'];

        if (!allowedExts.includes(ext)) {
            return res.status(400).json({ error: 'Only APK files allowed' });
        }

        if (fileData.length > 200 * 1024 * 1024) {
            return res.status(400).json({ error: 'File too large. Max 200MB.' });
        }

        let shortId;
        do {
            shortId = generateShortId();
        } while (db[shortId]);

        const filePath = path.join(UPLOAD_DIR, `${uuidv4()}${ext}`);
        fs.writeFileSync(filePath, fileData);

        db[shortId] = {
            originalName: fileName,
            filePath,
            fileSize: fileData.length,
            uploadDate: new Date().toISOString()
        };

        saveDb();

        const shortUrl = `https://${req.headers.host}/${shortId}`;

        res.json({
            success: true,
            shortId,
            shortUrl,
            fileName,
            fileSize: fileData.length
        });
    });

    bb.end(req.body);
};
