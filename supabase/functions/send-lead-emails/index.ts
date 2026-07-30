import "jsr:@supabase/functions-js/edge-runtime.d.ts";

Deno.serve(() => {
  return new Response("Gone", {
    status: 410,
    headers: {
      "Content-Type": "text/plain",
      "Cache-Control": "no-store",
    },
  });
});
