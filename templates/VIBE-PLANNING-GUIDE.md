# Vibe Planning Guide

> Example prompts for the vibe planning phase. These are meant to be free-form and unstructured.
> Adapt them to your project - these show the progression, not exact words to use.

---

## The Flow

Vibe planning is a conversation. You're exploring, not committing. The goal is to get on the same page with the AI about what to build before creating the structured plan.

---

## Example Prompts (in order)

### Prompt 1: Explore the codebase
```
Read [key files] and deeply understand how [existing feature] is built.
```
Why: Prime the AI with codebase knowledge before planning anything new.

### Prompt 2: Explore options
```
I want to build [feature description].
Explore our options for how we can build this, do any necessary research.

Report back the options in this format:
Option:
Description:
Tradeoffs:
Effort:
```
Why: Get multiple approaches before committing to one.

### Prompt 3: Refine the approach
```
What libraries/technologies would we need?
What else do we need to think about during this implementation?
I'm leaning toward option #X because [reason].
```
Why: Narrow down the approach, surface unknowns.

### Prompt 4: Add constraints
```
We also need to ensure [constraint].
[Specific requirement about security, platform support, etc.]
```
Why: Add guardrails before the plan is written.

### Prompt 5: Create the structured plan
```
Based on all the research we just did, create an implementation plan
in a file called requests/{feature}-plan.md.

Use the template in templates/STRUCTURED-PLAN-TEMPLATE.md.

Include all relevant information from our research so the coding agent
can reliably build the entire feature end to end including tests.
```
Why: Transition from vibe planning to structured plan. The AI writes the plan using the conversation as context.

---

## Tips

- You don't have to use all 5 prompts. Sometimes 2-3 are enough.
- Speak naturally. Use voice-to-text if it helps (AquaVoice, Open Whisper).
- The vibe planning conversation IS the Memory pillar of Context Engineering.
- Review the structured plan yourself before moving to implementation.
- **Verify context loading**: Ask the AI "Let me know what context you already have in this conversation" to confirm it loaded all on-demand context you expected.
- **After execution**: Ask for "a concise summary of what was implemented and advice for how I can run everything, including any environment changes needed after this feature."
- **Speed up on similar features**: Once trust is established and you're building something similar to a previous feature, you can skip vibe planning and go straight to `/planning`. Only do this after 10+ successful manual runs.
- **Do most research in vibe planning**, not in the planning command. Vibe planning is where you ask questions, explore options, and get on the same page. The planning command handles structured research to fill the template.
