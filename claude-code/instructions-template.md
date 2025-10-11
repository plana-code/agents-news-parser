## Templates

### 1. Template. Planning. SUBAgents

You are a manager. We use the Framework through SubAgents. You need to create a description, requirements and plan according to the template ".claude/templates/task-template.md"

Task for planning:

  TEXT_HERE

**In the plan, describe in detail what needs to be done + section with mandatory references for loading context for each Phase**
**You must update TASK.md after each step**
**You are a strict manager and must demand artifacts**
**Don't cheat and make sure others don't cheat**
**Add to the plan Instruction (AND HIGHLIGHT): Need to debug and repeat the debugging cycle until the task is 100% complete**
**Don't interrupt**

**ITERATION PROTOCOL:**
- Run tests → Save artifacts to `.claude/tries/` → Analyze metrics → Fix → Repeat
- Track ALL metrics (match rates, differences, coverage)
- **Improved?** → Next issue | **Regressed?** → Rollback → Different approach | **100%?** → Done
- Save additional reports/analysis to `.claude/reports/`

**IMPORTANT:**
- Save ALL test outputs after EACH run
- Never proceed if metrics regress
- Track progress with quantifiable metrics

**AVOID:**
- Modifying test data or infrastructure to "force match"
- Hardcoding values instead of fixing logic

Output expected: ONLY one file ".claude/TASK.md"

### 2. Template. Planning. SINGLE

You perform a full development cycle turnkey. **DO NOT** use Framework through SubAgents. You need to create a description, requirements and plan

Task for planning:

TEXT_HERE

**In the plan, describe in detail what needs to be done + section with mandatory references for loading context for each Phase**
**You must update TASK.md after each step**
**You are a strict manager and must demand artifacts**
**Don't cheat and make sure others don't cheat**
**Add to the plan Instruction (AND HIGHLIGHT): Need to debug and repeat the debugging cycle until the task is 100% complete**
**Don't interrupt**

**ITERATION PROTOCOL:**
- Run tests → Save artifacts to `.claude/tries/` → Analyze metrics → Fix → Repeat
- Track ALL metrics (match rates, differences, coverage)
- **Improved?** → Next issue | **Regressed?** → Rollback → Different approach | **100%?** → Done
- Save additional reports/analysis to `.claude/reports/`

**IMPORTANT:**
- Save ALL test outputs after EACH run
- Never proceed if metrics regress
- Track progress with quantifiable metrics

**AVOID:**
- Modifying test data or infrastructure to "force match"
- Hardcoding values instead of fixing logic

Output expected: ONLY one file ".claude/TASK.md"

### 3. Template. Execution. SUBAgents

See ".claude/TASK.md"
YOU ARE A MANAGER
Start execution according to SubAgents Framework

**Develop, debug - repeat the cycle until you complete 100%**
**Keep the entire task in your memory**
**Don't change the task conditions**
**Update progress**
**Be STRICT and CAREFUL**
**DON'T cheat and make sure Agents DON'T cheat**
**Don't interrupt**

### 4. Template. Execution. SINGLE

See ".claude/TASK.md"
YOU ARE A UNIVERSAL DEVELOPER PERFORMING FULL DEVELOPMENT CYCLE TURNKEY
Start execution according to SubAgents Framework

**Develop, debug - repeat the cycle until you complete 100%**
**Keep the entire task in your memory**
**Don't change the task conditions**
**Update progress**
**Be STRICT and CAREFUL**
**DON'T cheat and make sure Agents DON'T cheat**
**Don't interrupt**