---
description: Run a real multi-model council discussion via OpenCode dispatch (13 models)
agent: build
---

# Council: Multi-Model Discussion

Dispatch a question to **13 real AI models** across 4 providers and collect their responses. Uses the OpenCode server SDK — requires `opencode serve` running. All models run in parallel with 90s timeout each.

## Usage

```
/council <topic or question>
```

`$ARGUMENTS` — The topic, question, or decision to discuss.

---

## Step 1: Verify Server

Run this bash command to verify the OpenCode server is healthy:

```bash
bun -e "
import { createOpencodeClient } from '@opencode-ai/sdk/v2/client';
const client = createOpencodeClient({ baseUrl: 'http://127.0.0.1:4096' });
const h = await client.global.health();
console.log(h.data?.healthy ? 'HEALTHY' : 'UNHEALTHY');
"
```

**If UNHEALTHY or error:** Report "OpenCode server not running. Start with `opencode serve`." and stop.

---

## Step 2: Build the Council Prompt

Take the user's topic from `$ARGUMENTS` and wrap it:

```
You are participating in a multi-model council discussion with 12 other AI models.

TOPIC: {$ARGUMENTS}

Give your honest analysis, opinion, or answer. Be specific and concrete.
If this is a decision, state your recommendation and why.
If this is a review, give strengths, risks, and improvements.

Keep your response to 200-400 words. Be direct.
```

Store this as `COUNCIL_PROMPT`.

---

## Step 3: Write Prompt to Temp File

Write `COUNCIL_PROMPT` to a temp file so the bun script can read it cleanly (avoids escaping issues):

```bash
# Write the prompt to a temp file
cat > .opencode/.tmp/council-prompt.txt << 'PROMPT_EOF'
{COUNCIL_PROMPT content here}
PROMPT_EOF
```

---

## Step 4: Dispatch to 13 Models

Run this bash script. It reads the prompt from the temp file and dispatches to all 13 models in parallel:

```bash
bun -e "
import { createOpencodeClient } from '@opencode-ai/sdk/v2/client';
import { readFileSync } from 'node:fs';

const client = createOpencodeClient({ baseUrl: 'http://127.0.0.1:4096' });
const PROMPT = readFileSync('.opencode/.tmp/council-prompt.txt', 'utf-8');

const models = [
  // bailian-coding-plan-test (5 models — FREE)
  { providerID: 'bailian-coding-plan-test', modelID: 'qwen3.5-plus', label: 'Qwen-3.5-Plus' },
  { providerID: 'bailian-coding-plan-test', modelID: 'qwen3-coder-plus', label: 'Qwen-Coder-Plus' },
  { providerID: 'bailian-coding-plan-test', modelID: 'qwen3-max-2026-01-23', label: 'Qwen-3-Max' },
  { providerID: 'bailian-coding-plan-test', modelID: 'glm-5', label: 'BL-GLM-5' },
  { providerID: 'bailian-coding-plan-test', modelID: 'kimi-k2.5', label: 'BL-Kimi-K2.5' },
  // ollama-cloud (3 models — FREE)
  { providerID: 'ollama-cloud', modelID: 'deepseek-v3.2', label: 'DeepSeek-v3.2' },
  { providerID: 'ollama-cloud', modelID: 'qwen3.5:397b', label: 'OC-Qwen3.5-397B' },
  { providerID: 'ollama-cloud', modelID: 'kimi-k2-thinking', label: 'Kimi-K2-Thinking' },
  // zai-coding-plan (4 models — FREE)
  { providerID: 'zai-coding-plan', modelID: 'glm-5', label: 'ZAI-GLM-5' },
  { providerID: 'zai-coding-plan', modelID: 'glm-4.7', label: 'ZAI-GLM-4.7' },
  { providerID: 'zai-coding-plan', modelID: 'glm-4.5', label: 'ZAI-GLM-4.5' },
  { providerID: 'zai-coding-plan', modelID: 'glm-4.7-flash', label: 'ZAI-GLM-4.7-Flash' },
  // openai (1 model — PAID cheap)
  { providerID: 'openai', modelID: 'gpt-5.3-codex', label: 'GPT-5.3-Codex' },
];

console.log('Dispatching to ' + models.length + ' models in parallel...');
const startTime = Date.now();

const results = await Promise.allSettled(models.map(async (m) => {
  const sess = await client.session.create({ title: 'council-' + m.label });
  const sessionID = sess.data?.id;
  if (!sessionID) return { label: m.label, text: '[NO SESSION]', ms: 0 };
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  const t0 = Date.now();
  try {
    const result = await client.session.prompt({
      sessionID,
      model: { providerID: m.providerID, modelID: m.modelID },
      parts: [{ type: 'text', text: PROMPT }],
    }, { signal: controller.signal });
    clearTimeout(timeout);
    const parts = result?.data?.parts;
    let text = '';
    if (Array.isArray(parts)) {
      for (const p of parts) { if (p.type === 'text') text += p.text; }
    }
    return { label: m.label, text: text || '[EMPTY RESPONSE]', ms: Date.now() - t0 };
  } catch (e) {
    clearTimeout(timeout);
    const aborted = e?.name === 'AbortError' || controller.signal.aborted;
    return { label: m.label, text: aborted ? '[TIMEOUT after 90s]' : '[ERROR: ' + e.message + ']', ms: Date.now() - t0 };
  } finally {
    try { await client.session.delete({ sessionID }); } catch {}
  }
}));

const wallTime = Date.now() - startTime;
let responded = 0;
let failed = 0;

for (const r of results) {
  const v = r.status === 'fulfilled' ? r.value : { label: '?', text: '[PROMISE REJECTED]', ms: 0 };
  const ok = !v.text.startsWith('[');
  if (ok) responded++; else failed++;
  console.log('');
  console.log('=== ' + v.label + ' (' + v.ms + 'ms) ' + (ok ? 'OK' : 'FAILED') + ' ===');
  console.log(v.text);
}

console.log('');
console.log('=== COUNCIL SUMMARY ===');
console.log('Models: ' + models.length + ' | Responded: ' + responded + ' | Failed: ' + failed + ' | Wall time: ' + wallTime + 'ms');
"
```

**Timeout:** 90 seconds per model. All 13 run in parallel so wall time is ~90s max regardless of count.

---

## Step 5: Present Results

After the script runs, read the output and format as a structured synthesis:

### Response Summary Table

| # | Model | Provider | Status | Key Point |
|---|-------|----------|--------|-----------|
| 1 | Qwen-3.5-Plus | bailian | OK/FAIL | {1-line summary} |
| 2 | Qwen-Coder-Plus | bailian | OK/FAIL | {1-line summary} |
| ... | ... | ... | ... | ... |

### Consensus Analysis

Group responses by theme:

- **Strong agreement** (8+ models): {what they agree on}
- **Moderate agreement** (5-7 models): {what most agree on}
- **Split opinions** (<5 models per side): {where they disagree}
- **Unique insights** (1-2 models only): {novel points worth considering}

### Provider Perspective Comparison

| Aspect | Bailian Models | Ollama Models | ZAI Models | GPT |
|--------|---------------|---------------|------------|-----|
| Direction | ... | ... | ... | ... |
| Risk identified | ... | ... | ... | ... |
| Recommendation | ... | ... | ... | ... |

### Final Synthesis

{Opus synthesizes across all 13 responses: what's the answer/recommendation?}

---

## Step 6: Save Artifact (Optional)

If the council is for an important decision, save to `requests/council-discussions/{topic-slug}.md`.

---

## Council Models (13 total)

### bailian-coding-plan-test (5 models — FREE)

| Model | Family | Strength |
|-------|--------|----------|
| qwen3.5-plus | Qwen | Strong reasoning, broad knowledge |
| qwen3-coder-plus | Qwen | Code-specialized with thinking |
| qwen3-max-2026-01-23 | Qwen | Largest Qwen, best quality |
| glm-5 | GLM | Thinking/reasoning model |
| kimi-k2.5 | Kimi | Long context, factual recall |

### ollama-cloud (3 models — FREE)

| Model | Family | Strength |
|-------|--------|----------|
| deepseek-v3.2 | DeepSeek | Independent family, strong reasoning |
| qwen3.5:397b | Qwen | Full-size Qwen 397B parameter model |
| kimi-k2-thinking | Kimi | Thinking/chain-of-thought model |

### zai-coding-plan (4 models — FREE)

| Model | Family | Strength |
|-------|--------|----------|
| glm-5 | GLM | Top-tier thinking model |
| glm-4.7 | GLM | Strong general coding |
| glm-4.5 | GLM | Stable, well-tested |
| glm-4.7-flash | GLM | Fast responses, good for quick takes |

### openai (1 model — PAID cheap)

| Model | Family | Strength |
|-------|--------|----------|
| gpt-5.3-codex | GPT | Strongest code reasoning, paid reference point |

---

## Notes

- **All 13 models run in parallel** — wall time is ~90s regardless of model count
- **Minimum 4 responses** needed for a valid council (out of 13, this is almost guaranteed)
- **Provider diversity** ensures different training data and reasoning approaches
- Models from the same provider (e.g., 4 ZAI GLM variants) provide version-diversity within a family
- **Cost**: 12 FREE + 1 PAID (GPT-5.3-codex). Total cost per council ≈ 1 GPT call

**When to use /council:**
- Architecture decisions with multiple valid approaches
- Process design or workflow changes
- Security-sensitive design reviews
- Validating decomposition (/decompose) output
- When you want diverse perspectives before committing to a direction

**When NOT to use:**
- Simple factual questions (use dispatch instead)
- Code review (use /code-loop cascade)
- Trivial decisions where one model suffices

---

## Output Presentation Rule

**MANDATORY: Present raw council output to the user FIRST.**

1. After all models respond, display each model's full response with its label and timing
2. Do NOT summarize, synthesize, or interpret results before showing them
3. Do NOT claim consensus that you inferred — let the user read the actual responses
4. Wait for the user to acknowledge they have read the output
5. Only provide analysis/summary if the user explicitly asks for it after reading

**Why this rule exists:** The orchestrator (Opus) has a tendency to fabricate consensus or prematurely summarize before the user sees the raw data. This undermines the entire purpose of running a multi-model council. The user must see the actual model outputs to make their own judgment.

---

## Council Discipline

**MANDATORY: One dispatch per question. No spam.**

1. Max 1 council dispatch per user question
2. Cap at 10 models per dispatch
3. For brainstorming: 4-5 models is sufficient
4. For architecture decisions: up to 10 models
5. Never re-run unless user explicitly says "run again"
6. Write dispatch script to .opencode/.tmp/, run once, read output
7. Clean up sessions after each run

**Why this rule exists:** The orchestrator (Opus) has a tendency to fire unlimited parallel sessions, creating 15+ model calls per question. This wastes resources and produces so much output that nobody can read it all.
