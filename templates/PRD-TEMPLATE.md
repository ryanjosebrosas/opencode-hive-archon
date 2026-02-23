# PRD Template (Product Requirements Document)

> Use this template to define the full scope of your MVP. The PRD completes Layer 1
> planning — it answers **what** you're building, while CLAUDE.md answers **how**.
>
> **Create this FIRST** for new projects. It guides everything: global rules,
> on-demand context, and individual feature plans (Layer 2).
>
> **Critical Warning**: Do NOT use this PRD as a single execution plan. Break it into
> granular Layer 2 plans (one per PIV loop). AI coding assistants get overwhelmed
> if you send the full scope into implementation at once.

---

# Product Requirements Document: {Product Name}

## Executive Summary

**{Product Name}** is {one sentence describing what the product does and for whom}.

**MVP Goal:** {One sentence defining the minimum viable product outcome.}

---

## Mission

{What the product does and why it matters. 2-3 sentences max.}

### Core Principles

1. **{Principle 1}** — {brief explanation}
2. **{Principle 2}** — {brief explanation}
3. **{Principle 3}** — {brief explanation}

---

## Target Users

**{User persona}** who want to:
- {Primary need 1}
- {Primary need 2}
- {Primary need 3}

**Technical Comfort Level:** {What level of technical knowledge is expected?}

---

## MVP Scope

### In Scope

**Core Functionality:**
- {Feature 1}
- {Feature 2}
- {Feature 3}

**Technical:**
- {Technical requirement 1}
- {Technical requirement 2}

**Integration:**
- {Integration point 1}

**Deployment:**
- {Deployment approach}

### Out of Scope (Future Considerations)

- {Feature explicitly excluded from MVP}
- {Feature explicitly excluded from MVP}
- {Feature explicitly excluded from MVP}

---

## User Stories

### Primary User Stories

1. **As a {user type}, I want to {action}**, so that {benefit}.
   - Example: "{concrete usage example}"

2. **As a {user type}, I want to {action}**, so that {benefit}.
   - Example: "{concrete usage example}"

3. **As a {user type}, I want to {action}**, so that {benefit}.
   - Example: "{concrete usage example}"

### Technical User Stories

4. **As a {user type}, I want to {action}**, so that {benefit}.
5. **As a {user type}, I want to {action}**, so that {benefit}.

---

## Core Architecture & Patterns

### Architecture: {Architecture Name}

```
project-root/
├── {directory structure showing key directories}
├── {and their purposes}
└── {keep it scannable}
```

### Key Patterns

**1. {Pattern Name}**
- {How this pattern works in the project}

**2. {Pattern Name}**
- {How this pattern works in the project}

**3. {Pattern Name}**
- {How this pattern works in the project}

---

## Technology Stack

### Backend / Frontend / Core
- **{Technology}** — {purpose}
- **{Technology}** — {purpose}
- **{Technology}** — {purpose}

### Optional Dependencies
- **{Technology}** — {purpose}

---

## Security & Configuration

### Authentication
{Describe auth approach for MVP — keep it simple.}

### Configuration Management

**Environment Variables (`.env`):**
```bash
# {Category}
VARIABLE_NAME=value  # Description

# {Category}
VARIABLE_NAME=value  # Description
```

### Security Scope

**In Scope:**
- {Security feature included in MVP}

**Out of Scope (Keep Simple):**
- {Security feature NOT in MVP}

---

## API Specification

### Endpoint: `{METHOD} {path}`

**Request:**
```json
{
  "example": "request body"
}
```

**Response:**
```json
{
  "example": "response body"
}
```

{Add more endpoints as needed.}

---

## Success Criteria

### MVP Success Definition

**Functional Requirements:**
- {Measurable criterion 1}
- {Measurable criterion 2}
- {Measurable criterion 3}

**Quality Indicators:**
- {Quality metric 1}
- {Quality metric 2}

**User Experience:**
- {UX goal 1}
- {UX goal 2}

---

## Implementation Phases

### Phase 1: {Phase Name} (Week {X})
**Goal:** {One sentence goal}

**Deliverables:**
- {Deliverable 1}
- {Deliverable 2}

**Validation:** {How to verify this phase is complete}

---

### Phase 2: {Phase Name} (Week {X})
**Goal:** {One sentence goal}

**Deliverables:**
- {Deliverable 1}
- {Deliverable 2}

**Validation:** {How to verify this phase is complete}

---

### Phase 3: {Phase Name} (Week {X})
**Goal:** {One sentence goal}

**Deliverables:**
- {Deliverable 1}
- {Deliverable 2}

**Validation:** {How to verify this phase is complete}

---

## Future Considerations (Post-MVP)

**Potential Enhancements:**
- {Enhancement 1}
- {Enhancement 2}
- {Enhancement 3}

**Integration Opportunities:**
- {Integration 1}
- {Integration 2}

---

## Risks & Mitigations

### Risk: {Risk Name}
**Mitigation:** {How to handle it}

### Risk: {Risk Name}
**Mitigation:** {How to handle it}

### Risk: {Risk Name}
**Mitigation:** {How to handle it}

---

## Appendix

### Related Documents
- {Link to detailed specs, tool designs, or reference materials}

### Key Dependencies
- {Dependency}: {URL}

### Repository Structure
```
project-root/
├── {final directory layout}
└── {showing where everything lives}
```
