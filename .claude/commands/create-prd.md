---
description: Generate a PRD from vibe planning conversation
argument-hint: [product-name]
---

# Create PRD: Generate Product Requirements Document

## Product

**Product Name**: $ARGUMENTS

## Mission

Transform the current vibe planning conversation into a **structured PRD** using the project's PRD template. The PRD defines **what** to build (scope, features, architecture, success criteria) — it is Layer 1 planning.

**Key Rules**:
- We do NOT write code in this phase. We are defining the product scope.
- Use the conversation context as the primary source of decisions and research.
- Fill every section of the template — no generic placeholders.

## Process

### 1. Review Conversation Context

Analyze everything discussed in this conversation:
- Product goals and vision
- Features discussed and agreed upon
- Architecture decisions made
- Technology choices and rationale
- Scope boundaries (what's in, what's out)
- User stories and personas explored

Ask the user to clarify anything that's ambiguous BEFORE writing the PRD.

### 2. Read the PRD Template

Read the template structure:
@templates/PRD-TEMPLATE.md

### 3. Generate the PRD

Fill every section of the template using:
- Decisions from the vibe planning conversation
- Research findings discussed
- User requirements stated
- Technical constraints identified

**Be specific, not generic.** Every section should contain real project details, not template placeholders.

### 4. Save the PRD

Save the completed PRD to: `reference/PRD.md`

This location makes it available as on-demand context — loaded when choosing the next feature to build.

## Output

After saving, report:
- Product name and PRD file path
- Number of features/user stories defined
- Key architectural decisions captured
- Suggested next steps:
  1. Review the PRD for accuracy
  2. Use `/init-c` to generate CLAUDE.md (global rules) informed by the PRD
  3. Create on-demand reference guides from the PRD
  4. Start first PIV loop: pick a feature from the PRD and run `/planning [feature]`
