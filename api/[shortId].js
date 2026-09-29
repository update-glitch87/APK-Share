const fs = require('fs');
const path = require('path');

const DB_FILE = '/tmp/db.json';

module.exports = async (req, res) => {
    const { shortId } = req.params;

    if (!fs.existsSync(DB_FILE)) {
        return res.status(404).send('File not found');
    }

    const db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
    const file = db[shortId];

    if (!file) {
        return res.status(404).send('File not found or link expired');
    }

    if (!fs.existsSync(file.filePath)) {
        return res.status(404).send('File not found on server');
    }

    const fileData = fs.readFileSync(file.filePath);

    res.setHeader('Content-Disposition', `attachment; filename="${file.originalName}"`);
    res.setHeader('Content-Type', 'application/vnd.android.package-archive');
    res.setHeader('Content-Length', fileData.length);
    res.send(fileData);
};
