/**
 * HostSeba cPanel Node.js Selector / Phusion Passenger Entrypoint for Next.js.
 * Located at: apps/web/server.js
 */
const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const dev = process.env.NODE_ENV !== 'production';
const hostname = process.env.HOSTNAME || '127.0.0.1';
const port = parseInt(process.env.PORT || '3000', 10);

const app = next({ dev, hostname, port, dir: __dirname });
const handle = app.getRequestHandler();

app.prepare()
  .then(() => {
    const server = createServer(async (req, res) => {
      try {
        const parsedUrl = parse(req.url, true);
        await handle(req, res, parsedUrl);
      } catch (err) {
        console.error('Error handling request:', req.url, err);
        res.statusCode = 500;
        res.end('Internal Server Error');
      }
    });

    server.once('error', (err) => {
      console.error('Next.js server error:', err);
      process.exit(1);
    });

    server.listen(port, () => {
      console.log(`> Next.js production server listening on http://${hostname}:${port}`);
    });
  })
  .catch((err) => {
    console.error('Failed to prepare Next.js application:', err);
    process.exit(1);
  });
