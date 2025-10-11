# TASK: [Task Title]

## 📋 Overview
[Brief description of what needs to be accomplished]

## 🎯 Critical Requirements
1. **[Requirement 1]**: [Details]
2. **[Requirement 2]**: [Details]
3. **[Additional numbered requirements as needed]**

## 📚 Required Context Files
**Agents MUST load ALL these files before starting:**

### [Category 1]
1. `path/to/file1.ext` - Description (line count if relevant)
2. `path/to/file2.ext` - Description

### [Category 2]
3. `path/to/file3.ext` - Description
4. `path/to/file4.ext` - Description

### [Additional categories as needed]

## 🚫 Constraints
- **NEVER** [constraint 1]
- **NEVER** [constraint 2]
- **MUST** [requirement 1]
- **MUST** [requirement 2]

## 🤖 Available Agents
**Core Agents:**
- **developer**: Implements features, writes code, fixes bugs
- **tester**: Creates tests, debug failures, runs test suites, analyzes coverage
- **reviewer**: Architectural reviews, code quality, best practices

**Project Agents:**
- **sql_expert**: PostgreSQL/ClickHouse expert for SQL queries, migrations, optimization

## 📁 Project Memory (Key Files)
**Configuration:**
- `CLAUDE.md` - Project instructions and commands
- `bootstrap.yml` / `application-dev.yml` - Spring Boot configuration
- `DataSourcesConfiguration.java` - Dual database setup

**SQL Schemas:**
- `src/test/resources/scripts/quotes_ddl_v3.sql` - ClickHouse schema
- `src/test/resources/scripts/pricing_postgres_complete_schema.sql` - PostgreSQL schema
- `src/test/resources/scripts/pg_table_structure.md` - PG table descriptions
- `src/test/resources/scripts/ch_table_structure.md` - CH table descriptions

**Core Services:**
- `PricingAnalyticsServiceImpl.java` - Main business logic
- `ReportingController.java` - REST API endpoints
- `QuoteAnalyticsRepositoryImpl.java` - Database queries

## 🔄 Execution Plan

### Phase 1: [Phase Name]
**Agent:** [developer/tester/reviewer/sql_expert]
**Files:** [List file numbers from Required Context Files]
**Tasks:**
- [Task 1]
- [Task 2]
- [Task 3]

**Output:** [Expected deliverables]
**Status:** ⏳ Pending

### Phase 2: [Phase Name]
**Agent:** [agent type]
**Files:** [file numbers]
**Tasks:**
- [Task 1]
- [Task 2]

**Output:** [Expected deliverables]
**Status:** ⏳ Pending

### [Additional phases as needed]

## 📈 Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]
- [ ] [Additional criteria as needed]

## 👔 Manager Protocol
**After EACH phase:**
1. Update phase status (✅/⏳/❌)
2. Document outcomes and issues
3. Adjust next phase if needed
4. Track iteration count
5. Ensure 100% completion

**Iteration tracking:**
- Iteration 1: [Date] - [Status]
- Iteration 2: [Date] - [Status]
- Continue until 100% complete

## 🏁 Definition of Done
- [ ] [Deliverable 1]
- [ ] [Deliverable 2]
- [ ] [Deliverable 3]
- [ ] [Additional deliverables]
- [ ] Code reviewed and approved
- [ ] Documentation updated

---
**Priority:** [HIGH/MEDIUM/LOW/CRITICAL] | **Status:** ⏳ PENDING | **Iterations:** 0/0

## 🎉 FINAL RESULT
**Task completed on [Date]**
- [Summary of achievements]
- [Key metrics]
- [Final outcome]