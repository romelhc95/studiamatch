const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const ROOT = process.env.STATIC_ROOT || '/app/web/out';
const MIME = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
};

http.createServer((req, res) => {
  const hostname = (req.headers.host || '').split(':')[0].toLowerCase();
  let requestPath;
  try {
    requestPath = decodeURIComponent(req.url.split('?')[0]);
  } catch {
    res.writeHead(400, { 'Content-Type': 'text/plain' });
    return res.end('Bad request');
  }
  const rootPath = path.resolve(ROOT);
  if (hostname === 'studiamatch.com' && (requestPath === '/admin' || requestPath.startsWith('/admin/'))) {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    return res.end('Not found');
  }
  let filePath = path.resolve(rootPath, `.${requestPath}`);
  if (filePath !== rootPath && !filePath.startsWith(`${rootPath}${path.sep}`)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    return res.end('Forbidden');
  }
  if (requestPath === '/admin' || requestPath === '/admin/login' || requestPath === '/admin/edit' || requestPath === '/admin/users') {
    res.writeHead(302, { Location: `${requestPath}/` });
    return res.end();
  }
  if (requestPath.endsWith('/')) filePath = path.join(filePath, 'index.html');
  const ext = path.extname(filePath).toLowerCase() || '.html';
  const relativePath = path.relative(rootPath, filePath);
  if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    return res.end('Forbidden');
  }
  fs.readFile(path.join(rootPath, relativePath), (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      return res.end('Not found');
    }
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(PORT, '0.0.0.0', () => {
  console.log(`Static server on ${PORT}`);
});
