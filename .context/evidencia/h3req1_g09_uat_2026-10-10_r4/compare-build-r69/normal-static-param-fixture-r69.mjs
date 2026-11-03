import { createServer } from 'node:http';

const institutions = [
  { id: '00000000-0000-0000-0000-000000000001', name: 'Universidad de Lima', slug: 'ulima' },
  { id: '00000000-0000-0000-0000-000000000002', name: 'Pontificia Universidad Católica del Perú', slug: 'pucp' },
  { id: '00000000-0000-0000-0000-000000000003', name: 'Universidad Peruana de Ciencias Aplicadas', slug: 'upc' },
  { id: '00000000-0000-0000-0000-000000000004', name: 'Universidad San Ignacio de Loyola', slug: 'usil' },
  { id: '00000000-0000-0000-0000-000000000005', name: 'Universidad Tecnológica del Perú', slug: 'utp' },
  { id: 'b0000000-0000-4000-8000-000000000001', name: 'Synthetic Institute', slug: 'mock' },
];
const courses = [
  ['20000000-0000-0000-0000-000000000011', institutions[0].id, 'Programa local H3 11', 'programa-local-h3-11', 'https://local.example.test/programas/11'],
  ['20000000-0000-0000-0000-000000000016', institutions[0].id, 'Programa local H3 16', 'programa-local-h3-16', 'https://local.example.test/programas/16'],
  ['20000000-0000-0000-0000-000000000021', institutions[0].id, 'Programa local H3 21', 'programa-local-h3-21', 'https://local.example.test/programas/21'],
  ['70000000-0000-0000-0000-000000000091', institutions[0].id, 'Analítica Aplicada', 'analitica-aplicada-60000000', 'https://synthetic.h3.example/programs/analitica-aplicada/'],
  ['20000000-0000-0000-0000-000000000012', institutions[1].id, 'Programa local H3 12', 'programa-local-h3-12', 'https://local.example.test/programas/12'],
  ['20000000-0000-0000-0000-000000000017', institutions[1].id, 'Programa local H3 17', 'programa-local-h3-17', 'https://local.example.test/programas/17'],
  ['20000000-0000-0000-0000-000000000022', institutions[1].id, 'Programa local H3 22', 'programa-local-h3-22', 'https://local.example.test/programas/22'],
  ['20000000-0000-0000-0000-000000000013', institutions[2].id, 'Programa local H3 13', 'programa-local-h3-13', 'https://local.example.test/programas/13'],
  ['20000000-0000-0000-0000-000000000018', institutions[2].id, 'Programa local H3 18', 'programa-local-h3-18', 'https://local.example.test/programas/18'],
  ['20000000-0000-0000-0000-000000000023', institutions[2].id, 'Programa local H3 23', 'programa-local-h3-23', 'https://local.example.test/programas/23'],
  ['20000000-0000-0000-0000-000000000014', institutions[3].id, 'Programa local H3 14', 'programa-local-h3-14', 'https://local.example.test/programas/14'],
  ['20000000-0000-0000-0000-000000000019', institutions[3].id, 'Programa local H3 19', 'programa-local-h3-19', 'https://local.example.test/programas/19'],
  ['20000000-0000-0000-0000-000000000024', institutions[3].id, 'Programa local H3 24', 'programa-local-h3-24', 'https://local.example.test/programas/24'],
  ['20000000-0000-0000-0000-000000000015', institutions[4].id, 'Programa local H3 15', 'programa-local-h3-15', 'https://local.example.test/programas/15'],
  ['20000000-0000-0000-0000-000000000020', institutions[4].id, 'Programa local H3 20', 'programa-local-h3-20', 'https://local.example.test/programas/20'],
  ['20000000-0000-0000-0000-000000000025', institutions[4].id, 'Programa local H3 25', 'programa-local-h3-25', 'https://local.example.test/programas/25'],
  ['a0000000-0000-4000-8000-000000000001', institutions[5].id, 'Synthetic Course', 'mock-course', 'https://synthetic.h3.example/programs/mock-course'],
].map(([id, institution_id, name, slug, url]) => ({ id, institution_id, name, slug, url }));

const server = createServer((request, response) => {
  const url = new URL(request.url || '/', 'http://127.0.0.1');
  response.setHeader('content-type', 'application/json; charset=utf-8');
  if (request.method !== 'GET') {
    response.writeHead(405).end('[]');
    return;
  }
  if (url.pathname === '/rest/v1/institutions') {
    const slug = url.searchParams.get('slug') || '';
    const rows = slug.startsWith('eq.') ? institutions.filter((row) => row.slug === slug.slice(3)) : institutions;
    response.writeHead(200).end(JSON.stringify(rows));
    return;
  }
  if (url.pathname === '/rest/v1/courses_public_effective') {
    const institutionId = url.searchParams.get('institution_id') || '';
    const slug = url.searchParams.get('slug') || '';
    const rows = courses.filter((row) =>
      (!institutionId || institutionId === `eq.${row.institution_id}`)
      && (!slug || slug === `eq.${row.slug}`));
    response.writeHead(200).end(JSON.stringify(rows));
    return;
  }
  response.writeHead(404).end('[]');
});

server.listen(3363, '127.0.0.1', () => {
  process.stdout.write('fixture=ready|bind=127.0.0.1:3363|institutions=6|courses=17\n');
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
