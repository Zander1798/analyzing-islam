const fs = require('fs');
const path = require('path');

const batchFile = process.argv[2];
const startIdx = parseInt(process.argv[3] || '0');
const endIdx = parseInt(process.argv[4] || '5');

const data = JSON.parse(fs.readFileSync(batchFile, 'utf8'));
for (let i = startIdx; i < Math.min(endIdx, data.length); i++) {
    console.log(`\n=== ENTRY ${i}: ${data[i].id} ===`);
    console.log(data[i].html);
}
