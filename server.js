// Local, read-only bridge to the Relate graph. No network binding beyond localhost.
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { execFile } = require('node:child_process');
const root = __dirname;
const backend = path.join(root, 'ideenkarte.py');
const python = process.env.IDEENKARTE_PYTHON || (process.platform === 'win32' ? 'py' : 'python3');
const args = process.platform === 'win32' && !process.env.IDEENKARTE_PYTHON ? ['-3', backend, 'graph'] : [backend, 'graph'];
const files = {'/': ['index.html','text/html; charset=utf-8'], '/app.js':['app.js','text/javascript; charset=utf-8'], '/style.css':['style.css','text/css; charset=utf-8']};
const server = http.createServer((req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  if (req.method !== 'GET') { res.writeHead(405); return res.end(); }
  const pathname = new URL(req.url, 'http://localhost').pathname;
  if (pathname === '/api/graph') {
    return execFile(python, args, {timeout: 45000, maxBuffer: 1024*1024, windowsHide: true}, (err, stdout, stderr) => {
      if (err) { res.writeHead(503, {'Content-Type':'application/json; charset=utf-8'}); return res.end(JSON.stringify({error:'Relate-Daten konnten nicht geladen werden. Prüfe Datenbank und lokale Installation.', detail: stderr.trim() || err.message})); }
      try { const graph = JSON.parse(stdout); res.writeHead(200, {'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify(graph)); }
      catch (_) { res.writeHead(502, {'Content-Type':'application/json; charset=utf-8'}); res.end(JSON.stringify({error:'Ungültige Antwort der Relate-Abfrage.'})); }
    });
  }
  const file = files[pathname];
  if (!file) { res.writeHead(404); return res.end('Not found'); }
  fs.readFile(path.join(root, file[0]), (err, data) => { if (err) {res.writeHead(500); return res.end('Error');} res.writeHead(200, {'Content-Type':file[1]}); res.end(data); });
});
server.listen(Number(process.env.PORT || 5187), '127.0.0.1', () => console.log(`Ideenkarte: http://127.0.0.1:${server.address().port}`));

