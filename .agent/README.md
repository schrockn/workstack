# .agent - Agent-Optimized Documentation

**⚠️ These files are maintained for AI coding assistants and may be regenerated from source code.**

This directory contains comprehensive, agent-friendly documentation for the workstack codebase. While these files are currently version-controlled, they may be regenerated in the future to stay in sync with the codebase.

---

## 🚀 Quick Start (Choose Your Path)

### Path 1: Ultra-Fast Start (500 tokens)

**For experienced agents who know the codebase**

1. Read **RULES_CARD.md** (~500 tokens)
2. Start coding

**Best for**: Quick refresher, tight token budget

---

### Path 2: Quick Start (4,000 tokens)

**For new tasks on familiar codebase**

1. Read **CHEATSHEET.md** (~2,000 tokens) - Rules + common mistakes
2. Read **GLOSSARY.md** (~2,000 tokens) - Terminology
3. Start coding

**Best for**: Starting new feature, debugging issues

---

### Path 3: Comprehensive Start (8,000 tokens)

**For first time working with codebase**

1. Read **CHEATSHEET.md** (~2,000 tokens) - Rules overview
2. Read **ARCHITECTURE.md** (~4,000 tokens) - System design
3. Read **GLOSSARY.md** (~2,000 tokens) - Terminology
4. Consult specific sections of **PATTERNS.md** as needed (~200-500 each)

**Best for**: Learning the codebase, major refactoring

---

### Path 4: On-Demand Details

**After reading CHEATSHEET, consult as needed:**

- **docs/PATTERNS.md** (~8,500 tokens) - Detailed pattern explanations
- **docs/EXCEPTION_HANDLING.md** (~5,000 tokens) - Exception handling deep dive
- **tools/gt.md** (~7,000 tokens) - Graphite (gt) mental model
- **FEATURE_INDEX.md** (~3,000 tokens) - Find implementation locations
- **docs/MODULE_MAP.md** - Module structure details

---

## 📚 Document Index

### Quick References (Read First)

| Document          | Tokens | Purpose                      | When to Read           |
| ----------------- | ------ | ---------------------------- | ---------------------- |
| **RULES_CARD.md** | ~500   | Ultra-compact rules          | Quick reminder         |
| **CHEATSHEET.md** | ~2,000 | Rules + mistakes + templates | Every task             |
| **GLOSSARY.md**   | ~2,000 | Terminology definitions      | When confused by terms |

### Architecture & Design

| Document             | Tokens | Purpose                         | When to Read            |
| -------------------- | ------ | ------------------------------- | ----------------------- |
| **ARCHITECTURE.md**  | ~4,000 | System design, patterns, layers | Understanding structure |
| **FEATURE_INDEX.md** | ~3,000 | Feature → file mapping          | Finding implementations |

### Detailed References (As Needed)

| Document                       | Tokens | Purpose                    | When to Read           |
| ------------------------------ | ------ | -------------------------- | ---------------------- |
| **docs/PATTERNS.md**           | ~8,500 | Detailed code patterns     | Learning how to code   |
| **docs/EXCEPTION_HANDLING.md** | ~5,000 | Exception handling guide   | Understanding LBYL     |
| **tools/gt.md**                | ~7,000 | Graphite (gt) mental model | Working with gt/stacks |
| **docs/QUICK_REFERENCE.md**    | ~500   | One-line examples          | Ultra-quick lookup     |
| **docs/MODULE_MAP.md**         | -      | Module organization        | Navigating codebase    |

### Testing

| Document            | Tokens | Purpose          | When to Read  |
| ------------------- | ------ | ---------------- | ------------- |
| **tests/CLAUDE.md** | ~3,000 | Testing patterns | Writing tests |

---

## 🎯 Use Case Guide

### "I need to add a new command"

1. **CHEATSHEET.md** - See "Add Command" pattern
2. **docs/PATTERNS.md** (CLI section) - Detailed examples
3. **FEATURE_INDEX.md** - Find similar command to copy

### "I'm getting test failures"

1. **CHEATSHEET.md** - Check common mistakes
2. Look at error in "Common Errors" table
3. **docs/EXCEPTION_HANDLING.md** - If exception-related

### "I need to understand the architecture"

1. **GLOSSARY.md** - Learn terminology first
2. **ARCHITECTURE.md** - System design
3. **docs/MODULE_MAP.md** - Module details

### "I want to understand a specific pattern"

1. **CHEATSHEET.md** - Quick overview
2. **docs/PATTERNS.md** - Full explanation with rationale

### "I need to work with Graphite/gt commands"

1. **tools/gt.md** - Complete gt mental model and command reference

---

## 💡 Pro Tips

### Token Optimization

- Start with **RULES_CARD** or **CHEATSHEET** (saves 94-76% vs reading PATTERNS)
- Read PATTERNS sections **individually** (~200-500 tokens each)
- Use GLOSSARY as reference, don't memorize

### First Time Here?

Read in this order:

1. CHEATSHEET.md (understand the rules)
2. GLOSSARY.md (learn the terminology)
3. ARCHITECTURE.md (see the big picture)
4. Start coding with PATTERNS as reference

### Experienced with Codebase?

Read in this order:

1. RULES_CARD.md (quick reminder)
2. Code with CHEATSHEET as reference

---

## 📖 Core Documentation

### Quick References

- **RULES_CARD.md** - Ultra-compact rules (500 tokens)
- **CHEATSHEET.md** - Quick reference with common mistakes (2K tokens)
- **GLOSSARY.md** - Terminology and concept definitions

### Architecture

- **ARCHITECTURE.md** - System architecture, design patterns, component relationships
- **FEATURE_INDEX.md** - Complete index of features with implementation locations
- **docs/MODULE_MAP.md** - Module structure and exports

### Patterns & Standards

- **docs/PATTERNS.md** - Detailed code patterns and examples
- **docs/EXCEPTION_HANDLING.md** - Complete exception handling guide
- **docs/QUICK_REFERENCE.md** - One-line pattern examples

### Testing

- **tests/CLAUDE.md** - Testing patterns and practices

---

## 🔍 Finding Information

### "Where is feature X implemented?"

→ **FEATURE_INDEX.md**

### "What does term Y mean?"

→ **GLOSSARY.md**

### "How do I implement pattern Z?"

→ **CHEATSHEET.md** (quick) or **docs/PATTERNS.md** (detailed)

### "Why does this codebase do X differently?"

→ **ARCHITECTURE.md** (design decisions)

### "How do I write tests?"

→ **tests/CLAUDE.md**

---

## ⚠️ Important Notes

- Always cross-reference with actual source code, as implementations may evolve
- When in doubt, find similar existing code and copy its pattern
- All documentation links to specific line numbers in source files where applicable
- Token estimates are approximate - actual counts may vary ±10%

---

**Remember**: The goal is token efficiency. Start small (RULES_CARD or CHEATSHEET), expand as needed.
