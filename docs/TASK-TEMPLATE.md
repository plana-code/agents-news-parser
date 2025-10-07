# TASK: [TASK NAME]

## 🎯 GOAL & DESCRIPTION
[Clear description of what needs to be done]

## 👥 ROLES & RESPONSIBILITIES

### MANAGER (Main Agent)
**Responsibilities:**
- ✅ Orchestrate entire process
- ✅ Delegate tasks to agents
- ✅ Update this document
- ✅ Monitor execution
- ❌ NEVER writes code directly

### AGENTS
| Agent | Role | Responsibility |
|-------|------|----------------|
| **developer** | Developer | Code, features, bugs, refactoring |
| **tester** | Tester | Tests, coverage, reports |
| **reviewer** | Architect | Review, architecture, quality |

**⚠️ IMPORTANT: Only MANAGER updates TASK.md**

## 📋 REQUIREMENTS

### Functional
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

### Technical
- **Stack**: [technologies]
- **Constraints**: [limitations]
- **Integrations**: [external systems]

## 📚 MANDATORY CONTEXT
**Files to load before work:**
```
# Configuration
- /path/to/application.yml
- /path/to/config/database.yml

# Core classes
- /src/main/service/CoreService.java
- /src/main/controller/MainController.java

# Data models
- /src/main/entity/User.java
- /src/main/dto/UserRequest.java

# Tests (for reference)
- /src/test/service/CoreServiceTest.java

# Documentation
- /docs/api-spec.md
```

## 🔄 EXECUTION PLAN

### PHASE 1: [Name]
**Agent**: developer
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
  **Output**: [what will be ready]

### PHASE 2: [Name]
**Agent**: tester
- [ ] Task 1
- [ ] Task 2
  **Output**: [what will be ready]

### PHASE 3: [Name]
**Agent**: reviewer
- [ ] Task 1
- [ ] Task 2
  **Output**: [what will be ready]

### PHASE 4: Final Check
**Agent**: MANAGER
- [ ] All requirements met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## ✅ ACCEPTANCE CRITERIA
1. [Criterion 1 - measurable]
2. [Criterion 2 - measurable]
3. [Criterion 3 - measurable]

## 📊 STATUS UPDATES

### UPDATE FORMAT (MANDATORY)
```
PHASE: [number]
AGENT: [developer/tester/reviewer/manager]
TIME: [YYYY-MM-DD HH:MM]
COMPLETED:
✅ [what's done]
✅ [what's done]
ISSUES:
❌ [if any]
ARTIFACTS: (optional)
📁 [path to created/modified files]
📊 [path to reports]
📝 [path to documentation]
NEXT STEP:
→ [what's next]
→ Handoff to: [who]
```

### UPDATE HISTORY

#### Update #1
```
PHASE: 1
AGENT: manager
TIME: [time]
COMPLETED:
✅ Task distributed
✅ Plan approved
✅ Context loaded
ARTIFACTS:
📁 TASK.md
NEXT STEP:
→ developer starts implementation
```

## 🚨 RISKS & BLOCKERS
| Risk/Blocker | Impact | Solution | Status |
|--------------|--------|----------|--------|
| [description] | High/Medium/Low | [action] | Open/Resolved |

## 📁 ARTIFACTS
- **Code**: [path to files]
- **Tests**: [path to tests]
- **Docs**: [path to docs]
- **Reports**: [path to reports]

## ✔️ FINAL CHECKLIST
- [ ] All requirements implemented
- [ ] Code reviewed
- [ ] Tests written and passing
- [ ] Test coverage > 80%
- [ ] Documentation updated
- [ ] No critical issues from reviewer

## 🏁 RESULT
**Status**: ⏳ In Progress / ✅ Complete / ❌ Blocked
**Completion Date**: [date]
**Final Assessment**: [result description]

---
**RULES:**
1. Only MANAGER updates this file
2. Agents report to manager, don't modify TASK.md
3. Each phase must have measurable output
4. All updates in chronological order
5. Use ONLY specified report format