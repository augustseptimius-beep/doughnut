// Delte typer til projektvurderingslaget
// Bruges i VurderingBoks, VurderingPrintView, ScoreBars og client.tsx

export type VurderingScore = "groen" | "gul" | "roed" | null;

export interface VurderingEntry {
  score: VurderingScore;
  argumentation: string;
}

export interface Projektvurdering {
  projektnavn: string;
  beskrivelse: string;
  kommune_navn: string;
  vurderinger: Record<string, VurderingEntry>;
}
