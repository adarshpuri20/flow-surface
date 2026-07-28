# Code Review — ca90ca2c94

**Reviewed:** 2026-07-28T15:08:20-07:00
**Change:** `refactor(app-store): move credential query to repository pattern (#29724)` — base `ca90ca2^`, head `HEAD` (single commit)
**Files:** 2 changed — `packages/app-store/repositories/PrismaCredentialRepository.ts` (new), `packages/app-store/server.ts` (modified)
**Config:** no `.flow-surface.json` — stack-neutral defaults
**Blast radius:** LOW — single function (`getLocationGroupedOptions`), two consumers (`packages/trpc/server/routers/viewer/apps/locationOptions.handler.ts`, `packages/features/eventtypes/lib/getEventTypeById.ts`); moved query verified byte-for-byte identical; the one behavior delta is unobservable in this tree (verified end-to-end by Gates 4, 10, 11)

## Gate results

| Gate | Verdict | Findings | Notes (evidence) |
| :--- | :--- | :--- | :--- |
| 1 Architecture | CONCERNS | 1 HIGH, 1 MEDIUM, 1 LOW | Duplicates DI-registered `CredentialRepository` (`packages/features/di/modules/Credential.ts` binds `DI_TOKENS.CREDENTIAL_REPOSITORY`); ~30 repository constructors checked — all use `PrismaClient`, none `typeof prisma` |
| 2 Security | APPROVE | 1 MEDIUM, 1 LOW | Select relocation verified identical; `key`/`encryptedKey` (from `credentialForCalendarServiceSelect`, `packages/prisma/selects/credential.ts:3-18`) never reach either consumer's return shape; no injection vector (structured Prisma args only) |
| 3 Performance | APPROVE | 0 | Old inline query vs repository method compared field-by-field: byte-for-byte equivalent where/select; `buildNonDelegationCredentials` is a pure O(n) map |
| 4 Correctness | CONCERNS | 3 MEDIUM, 1 LOW | User branch now receives built credentials — traced through identity stub (`packages/app-store/delegationCredential.ts:95-99`) and `getApps`/`isDelegationCredential`: no field-presence branching, output unchanged today. `tsc` not runnable (no node_modules); manual generic trace found no type errors. Biome violations confirmed via `git diff --check` + `biome.json` |
| 5 Test coverage | CONCERNS | 1 MEDIUM, 1 LOW | Zero tests added; no pre-existing test reaches this path (repo-wide grep: 3 non-test refs to `getLocationGroupedOptions`), so nothing was silently bypassed; untested repositories match local convention (`CredentialRepository` also has no direct unit test) |
| 6 Cross-file deps | CONCERNS | 1 LOW | No cycles (`packages/lib/delegationCredential.ts` has zero imports); all new import edges pre-existed in `server.ts`; split `import type` lines vs merged convention; note: package `lint` script runs `biome lint`, not `biome check`, so format drift won't fail CI |
| 7 Isolation | APPROVE | 0 | All three `idToSearchObject` shapes (`{userId}`, `{teamId}`, `{teamId:{in:[teamId, org.id]}}`) preserved; spread-then-literal merge order byte-identical to pre-refactor; repository stateless, instantiated per call; single call site confirmed by grep |
| 8 Data freshness | APPROVE | 0 | No cache anywhere on the path (handler is bare `authedProcedure.query`, no `unstable_cache`/Accelerate directives touched); `buildNonDelegationCredential` returns new objects via spread — no input mutation |
| 9 Dead paths | APPROVE | 1 LOW | Every import in both files used; `buildNonDelegationCredentials` (~7 other importers) and `credentialForCalendarServiceSelect` (~30) not orphaned; removed TODO leaves no dangling references; if/else equivalence is pre-existing CE-stub dormancy, not new dead code |
| 10 Interface contract | CONCERNS | 1 MEDIUM, 2 LOW | `getLocationGroupedOptions` return shape (`{label, options:[…]}[]`) untouched (construction code byte-identical); no `.output()` zod schema on the tRPC procedure; empty/error paths propagate identically (no try/catch added or removed) |
| 11 Regression risk | CONCERNS | 1 MEDIUM, 1 LOW | `delegatedTo`/`delegatedToId`/`delegationCredentialId` never survive into either consumer's returned shape; `getEnabledAppsFromCredentials` reads only `id`/`appId`/`userId`/`teamId`; no real (non-stub) enrich implementation exists anywhere in this tree (`packages/features/ee` absent, `apps/api/v2` and `packages/platform/libraries/app-store.ts` checked) — risk is latent, upstream-sync-only |

## Surface smoothness

**NOT SMOOTH (unconverged) — accepted carry risk under the LOW-blast-radius stopping rule.**

- Iteration 1: the single HIGH fix (fold `findNonDelegationCredentialsByAppCategories` into the canonical `CredentialRepository`, rewire `server.ts`, delete the duplicate file) was fully specified and verified non-deforming (additive instance method, no name collision among the class's 24 methods, dependency edge `app-store -> @calcom/features/credentials` already used by 9 app-store files, DI binding unaffected). **Application was declined by the session's write-permission gate**, so the fix is recorded below rather than applied. No worktree lane was used (iterations 2–3 not reached — the block is a permissions gate, not a failed fix).
- No `smoothness-achieved` artifact is written: the change has not converged.
- Stopping rule: blast radius LOW + NOT SMOOTH → **ship, record in the debt ledger** (see Known debt carried forward).
- Surface-aware MEDIUM escalation check: no MEDIUM finding's proposed fix deforms neighbouring flows (doc-comment/test additions and formatting are inert; the `buildNonDelegationCredentials` cast fix touches a shared helper but is type-only and narrowing-safe — deferred anyway as inherited debt because no typecheck is runnable in this checkout). No escalations to BLOCK.

## Overall verdict

**APPROVE_WITH_NOTES** — no live correctness, security, isolation, freshness, or contract regression found by any gate. One HIGH architectural finding (duplicate repository) and a latent behavioral widening are carried as recorded debt with a ready-to-apply remediation.

## Findings by severity

### CRITICAL
None.

### HIGH
1. **Duplicate/competing credential repository** (Gate 1) — `packages/app-store/repositories/PrismaCredentialRepository.ts` creates a second repository for the `Credential` entity when a canonical, DI-registered `CredentialRepository` already exists (`packages/features/credentials/repositories/CredentialRepository.ts`; DI module `packages/features/di/modules/Credential.ts`) and is already imported by 9 files inside `packages/app-store` (e.g. `packages/app-store/delegationCredential.ts:1`). Fragments the single source of truth for credential queries and bypasses the DI container. Per-package `repositories/` dirs are legitimate for app-specific entities (e.g. `salesforce/lib/repositories/PrismaAssignmentReasonRepository.ts`) — the problem is duplicating an entity that already has a shared home.
   **Remediation (specified, verified feasible, NOT applied — write permission declined):**
   - Add to `CredentialRepository` (instance method, after `findByIdWithDelegationCredential`), with a doc comment noting it forces `delegatedTo`/`delegatedToId`/`delegationCredentialId` to `null` for all callers:
     `async findNonDelegationCredentialsByAppCategories({ idToSearchObject, appCategories }: { idToSearchObject: Prisma.CredentialWhereInput; appCategories: AppCategories[] })` — body identical to the current new file (same where/select, `return buildNonDelegationCredentials(credentials)`), using `this.prismaClient`.
   - Extend that file's imports: `buildNonDelegationCredentials` alongside `buildNonDelegationCredential`; `AppCategories` in the type import from `@calcom/prisma/client`.
   - In `packages/app-store/server.ts`: replace the `./repositories/PrismaCredentialRepository` import with `import { CredentialRepository } from "@calcom/features/credentials/repositories/CredentialRepository";`, instantiate `new CredentialRepository(prisma)`, and strip the trailing whitespace on lines 64, 65, 67, 83.
   - Delete `packages/app-store/repositories/PrismaCredentialRepository.ts` (directory becomes empty).
   - Resolves MEDIUM #4 (constructor typing) and MEDIUM #5's new-file half as side effects.

### MEDIUM
2. **Delegation-field nulling silently widened to the user branch** (Gates 4 + 11, same root) — `buildNonDelegationCredentials` overwrites `delegationCredentialId` with `null` (destroying the real DB value, `packages/lib/delegationCredential.ts:12-27`); pre-refactor this ran only in the team branch, now it runs before both branches. Unobservable today (identity stub; downstream field-insensitive; fields never reach consumer output) but a real EE/upstream `enrichUserWithDelegationConferencingCredentialsWithoutOrgId` that reads `delegationCredentialId` off incoming rows would silently get `null` for every user-path credential. Fix: doc comment on the repository method (included in HIGH #1's remediation) + a regression test pinning the delta (see LOW #14).
3. **Unscoped, secret-returning, reusable method** (Gate 2) — accepts arbitrary `Prisma.CredentialWhereInput` with no internal ownership assertion while selecting `key`/`encryptedKey`. Sole call site passes server-trusted `userId`/`teamId` predicates; risk is future callers. Fix: require `{ userId } | { teamId }` discriminator or runtime-assert the predicate before querying.
4. **`typeof prisma` constructor typing** (Gate 1) — every other repository constructor in the codebase types the param `PrismaClient`. Moot once HIGH #1 is applied.
5. **Biome formatting violations** (Gates 4, 6) — new file: 4-space indent, trailing whitespace (lines 3, 11, 14, 15), missing semicolons (35, 38), missing `es5` trailing commas (23, 31), no final newline; `server.ts`: trailing whitespace added on lines 64, 65, 67, 83 (`git diff --check`). Won't fail CI (`lint` runs `biome lint`, not `biome check`) but fails `biome format --check` and is visibly inconsistent. Fix: `biome format --write` on both files (subsumed by HIGH #1's remediation).
6. **New repository class untested** (Gate 5) — no unit test; consistent with local convention (existing `CredentialRepository` also has no direct test; consumers `vi.mock()` it), so a gap to close, not a blocker.
7. **Stale return-type contract now public** (Gate 10, inherited) — `buildNonDelegationCredentials`' cast (`packages/lib/delegationCredential.ts:30-35`) omits `delegationCredentialId: null` though the runtime forces it, so the repository's return type statically claims `string | null` for an always-null field. Pre-existing helper defect, first formalized as a reusable contract by this commit. Fix: derive the plural's element type from the singular's return type.

### LOW
8. Raw `Prisma.CredentialWhereInput` leaks the persistence type through the repository boundary (Gate 1) — majority convention here, but `IBookingRepository`'s decoupled `BookingWhereInput` is the stricter precedent to follow when folding into `CredentialRepository`.
9. Pre-existing: `credentialForCalendarServiceSelect` includes `key`/`encryptedKey`; verified not exposed beyond the server path (Gate 2). Unchanged by this commit.
10. Pre-existing: `getLocationGroupedOptions` has no test coverage before or after; nothing was silently bypassed (Gate 5).
11. Two separate `import type` lines from `@calcom/prisma/client` instead of one merged import (Gate 6); editor-integrated `biome check --write` would coalesce.
12. `if (user)`/`else` branches are functionally equivalent under the CE identity stub — pre-existing dormant-but-intentional EE seam, not new dead code (Gate 9).
13. Naming: method name implies pure fetch but also transforms; param name `idToSearchObject` copied from the call-site local into a public API (Gate 10).
14. No regression test pins the user-branch nulling delta (Gate 11). Minimal test: assert the credentials array passed to the enrich fn has `delegationCredentialId: null` even when the DB row's value is non-null — would fail pre-refactor, documenting the intent.

## Inherited debt disposition

| Item | From | Status |
| :--- | :--- | :--- |
| `key`/`encryptedKey` in `credentialForCalendarServiceSelect` | Pre-existing select, relocated verbatim | Carried — verified non-exposed end-to-end; revisit if the repository method gains new callers |
| `buildNonDelegationCredentials` cast omits `delegationCredentialId: null` | Pre-existing helper (`packages/lib/delegationCredential.ts:30-35`) | Carried — type-only fix deferred (no typecheck runnable in this checkout); fix before other modules consume the repository's return type |
| CE identity stub makes user/team branches equivalent | Pre-existing EE seam (`packages/app-store/delegationCredential.ts:95-99`) | Accepted — intentional community-edition placeholder |
| `getLocationGroupedOptions` untested | Pre-existing | Carried — see debt ledger |

## Known debt carried forward

| Item | Reason deferred | Revisit trigger |
| :--- | :--- | :--- |
| HIGH #1 duplicate repository (full remediation specified above) | Write permission declined in this session | Immediately, on next writable session — patch is ready to apply |
| MEDIUM #2 delegation-nulling widening (comment + regression test) | Same permission gate; test not runnable without install | With HIGH #1's application, or before any upstream sync touching `enrichUserWithDelegationConferencingCredentialsWithoutOrgId` |
| MEDIUM #3 unscoped where-input on secret-returning method | API design change beyond mechanical fix | Before `findNonDelegationCredentialsByAppCategories` gains a second caller |
| MEDIUM #5 Biome formatting drift | Same permission gate | With HIGH #1's application (`biome format --write`) |
| MEDIUM #6 / LOW #10 / LOW #14 missing tests | No install in this checkout; matches local convention | When the repository method gains callers or delegation logic goes live |
| MEDIUM #7 stale cast in shared helper | Type-only, unverifiable without typecheck here | Before external reuse of the repository's return type |
