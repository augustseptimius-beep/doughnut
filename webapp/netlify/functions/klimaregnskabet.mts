import type { Context, Config } from "@netlify/functions";

export default async (req: Request, context: Context) => {
  const url = new URL(req.url);
  const municipality = url.searchParams.get("municipality");
  const year = url.searchParams.get("year");
  const type = url.searchParams.get("type") ?? "Nøgletal";

  if (!municipality || !year) {
    return new Response(
      JSON.stringify({ error: "Mangler 'municipality' eller 'year' parameter" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  const apiKey = Netlify.env.get("KLIMAREGNSKABET_API_KEY");
  if (!apiKey) {
    return new Response(
      JSON.stringify({ error: "API-nøgle ikke konfigureret" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }

  const apiUrl = `https://klimaregnskabet.dk/api/municipality-data?municipality=${municipality}&year=${year}&type=${encodeURIComponent(type)}`;

  const response = await fetch(apiUrl, {
    headers: { "x-api-key": apiKey },
  });

  if (!response.ok) {
    return new Response(
      JSON.stringify({ error: `Klimaregnskabet API fejl: ${response.status}` }),
      { status: response.status, headers: { "Content-Type": "application/json" } }
    );
  }

  const data = await response.json();

  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
};

export const config: Config = {
  path: "/api/klimaregnskabet",
};
