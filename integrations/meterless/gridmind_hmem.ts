// GridMind <-> real Meterless H-MEM engine bridge.
// stdin : {"facts":[{content,source,tags?,confidence?}], "questions":[str], "feedback":"helpful|not_helpful|wrong"?}
// stdout: JSON with the engine's own retrieval trace, per-memory scores and trust-ledger entries.
// Every call goes through the engine services: MemoryStoreService.add, MemoryRetrievalService.query
// (hybrid ranking formula, AGENTS.md 6.1), feedback deltas (9.2) and TrustLedgerService.history (9).
import path from "node:path";
import { fileURLToPath } from "node:url";
import { HMEM } from "./vendor/hmem/src/index.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const stateDir = process.env.METERLESS_STATE_DIR ?? path.join(here, ".state");

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const c of process.stdin) chunks.push(c as Buffer);
  return Buffer.concat(chunks).toString("utf-8");
}

const req = JSON.parse(await readStdin());
const hmem = new HMEM({ persistDir: stateDir, actor: "gridmind-agent" });

const known = new Set(hmem.store.all().map((m) => m.source));
const added: string[] = [];
let skipped = 0;
for (const f of req.facts ?? []) {
  if (known.has(f.source)) { skipped++; continue; } // idempotent: one memory per source row
  const rec = hmem.add({
    content: f.content,
    type: "factual",
    layer: "working",
    tags: f.tags ?? [],
    confidence: f.confidence ?? 0.9,
    source: f.source,
  });
  known.add(f.source);
  added.push(rec.id);
}

const answers = [];
const cited = new Set<string>();
for (const q of req.questions ?? []) {
  const res = hmem.query(q, { threshold: 0.1, topN: req.topN ?? 5 });
  for (const r of res.memories) cited.add(r.memory.id);
  answers.push({
    question: q,
    strategy: res.trace.strategy,
    retrievalReason: res.trace.retrievalReason,
    scores: res.trace.scores,
    memories: res.memories.map((r) => ({
      id: r.memory.id,
      relevance: Number(r.relevance.toFixed(4)),
      content: r.memory.content,
      source: r.memory.source,
      layer: r.memory.layer,
      confidence: r.memory.confidence,
      tags: r.memory.tags,
    })),
    context: res.context,
  });
}

if (req.feedback) for (const id of cited) hmem.feedback(id, req.feedback); // operator verdict -> confidence delta

const ledger: Record<string, unknown[]> = {};
for (const id of cited) {
  ledger[id] = hmem.ledger.history(id).map((e) => ({
    action: e.action, actor: e.actor, at: new Date(e.timestamp).toISOString(),
    confidence: e.newState?.confidence ?? null,
  }));
}

console.log(JSON.stringify({
  engine: "Meterless H-MEM reference (vendor/hmem)",
  state_dir_is_persistent: true,
  memories_total: hmem.store.all().length,
  added: added.length,
  skipped_existing: skipped,
  answers,
  ledger,
}));
