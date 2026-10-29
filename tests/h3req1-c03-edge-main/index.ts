// Minimal, fixed-route equivalent of Supabase's main Edge service router.
// The actual admin-invite/index.ts runs in Edge Runtime's isolated user worker.
const FUNCTION_ROOT = '/candidate/supabase/functions';

Deno.serve(async (request: Request): Promise<Response> => {
  const { pathname } = new URL(request.url);
  if (pathname !== '/admin-invite') {
    return Response.json({ message: 'Function not found' }, { status: 404 });
  }

  try {
    const envVars = Object.entries(Deno.env.toObject());
    const worker = await EdgeRuntime.userWorkers.create({
      servicePath: `${FUNCTION_ROOT}/admin-invite`,
      memoryLimitMb: 150,
      workerTimeoutMs: 120_000,
      noModuleCache: false,
      importMapPath: null,
      envVars,
    });
    return await worker.fetch(request);
  } catch {
    return Response.json({ message: 'Function failed to start' }, { status: 503 });
  }
});
