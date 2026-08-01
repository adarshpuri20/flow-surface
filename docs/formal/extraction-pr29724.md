# Evidence extraction: the §5b component graph (cal.diy PR #29724)

The node and edge lists behind §5b's matrices, with the file:line evidence for every
claim. All citations refer to the public repository
[calcom/cal.diy](https://github.com/calcom/cal.diy) at two commits:

- **BASE (intended contract A\*):** `f3284f581ff18a37ecdcface587b4a03236b1861` (= `ca90ca2^`)
- **HEAD (actual A):** `ca90ca2c94536c7fac97e4e829cdfe18624c7f10`
  ([PR #29724](https://github.com/calcom/cal.diy/pull/29724), squash commit)

**Method.** Three independent extraction passes (the BASE graph, the HEAD graph, and
the DI system plus field readers), every line number derived by running `git grep -n` /
`git show` against a clone at the cited commit — never from memory. Every citation was
then independently re-checked against the commit content in a separate verification
pass: **127 of 127 evidence items confirmed, zero corrected line numbers.** Quotes
longer than 100 characters are verbatim prefixes or substrings of the cited line.

## Nodes

| id | file : symbol | exists at | evidence (file:line@commit) |
| :--- | :--- | :--- | :--- |
| `srv.getLocationGroupedOptions` | `packages/app-store/server.ts` : `getLocationGroupedOptions` | BASE + HEAD | server.ts:14@BASE, server.ts:13@HEAD |
| `srv.inlineCredentialQuery` | `packages/app-store/server.ts` : inline `prisma.credential.findMany` | **BASE only** | server.ts:65@BASE (findMany), :75 (select spread) |
| `repo.PrismaCredentialRepository.findNonDelegationCredentialsByAppCategories` | `packages/app-store/repositories/PrismaCredentialRepository.ts` | **HEAD only** | :7 (class), :10 (method), :18 (findMany), :28 (select spread), :38 (return build…) |
| `lib.buildNonDelegationCredentials` | `packages/lib/delegationCredential.ts` | BASE + HEAD | :30 (def); force-nulls `delegatedTo`/`delegatedToId`/`delegationCredentialId` at :24–26 |
| `appstore.enrichUserWithDelegationConferencingCredentialsWithoutOrgId` | `packages/app-store/delegationCredential.ts` | BASE + HEAD | :95 (def), :97–98 — **identity stub, body is `return user;`** |
| `appstore.getEnabledAppsFromCredentials` | `packages/app-store/_utils/getEnabledAppsFromCredentials.ts` | BASE + HEAD | :18 (def), :85 (default export); zero `delegationCredentialId` hits |
| `trpc.locationOptions.handler` | `packages/trpc/server/routers/viewer/apps/locationOptions.handler.ts` | BASE + HEAD | :14 (def); file byte-identical BASE↔HEAD (`git diff` empty) |
| `features.getEventTypeById` | `packages/features/eventtypes/lib/getEventTypeById.ts` | BASE + HEAD | :38 (def); file byte-identical BASE↔HEAD |
| `prisma.credential.table` | `packages/prisma/schema.prisma` : `model Credential` | BASE + HEAD | schema.prisma:308 |
| `select.credentialForCalendarServiceSelect` | `packages/prisma/selects/credential.ts` | BASE + HEAD | :3 (def); includes `delegationCredentialId`, `key`, `encryptedKey` |
| `features.CredentialRepository` | `packages/features/credentials/repositories/CredentialRepository.ts` | BASE + HEAD | :28 (class) — the pre-existing DI-managed credential repository |
| `di.CredentialModule` | `packages/features/di/modules/Credential.ts` | BASE + HEAD | :8 (token), :10 (bind), :14 (`classs: CredentialRepository` — sic, literal property name); token defined at `packages/features/di/tokens.ts:62` |
| `features.BookingAuditViewerService` | `packages/features/booking-audit/lib/service/BookingAuditViewerService.ts` | HEAD (checked) | :69 (class), :87 (deps.credentialRepository) — the concrete DI consumer |

## Edges at BASE (intended contract A\*)

All `static`.

| from → to | mechanism | evidence @BASE |
| :--- | :--- | :--- |
| `trpc.locationOptions.handler` → `srv.getLocationGroupedOptions` | import + await call | handler.ts:1 (import), :19 (call) |
| `features.getEventTypeById` → `srv.getLocationGroupedOptions` | import + await call | getEventTypeById.ts:3 (import), :202 (call) |
| `srv.getLocationGroupedOptions` → `srv.inlineCredentialQuery` | inline statement in function body | server.ts:65 |
| `srv.getLocationGroupedOptions` → `appstore.enrichUser…` | **if-user branch only** | server.ts:85 (`if (user) {`), :87 (call), :3 (import) |
| `srv.getLocationGroupedOptions` → `lib.buildNonDelegationCredentials` | **else branch only** | server.ts:96 (`} else {`), :98 (call), :5 (import) |
| `srv.getLocationGroupedOptions` → `appstore.getEnabledAppsFromCredentials` | call on merged list | server.ts:101 (call), :11 (import) |
| `srv.inlineCredentialQuery` → `prisma.credential.table` | `prisma.credential.findMany` | server.ts:65; schema.prisma:308 |
| `srv.inlineCredentialQuery` → `select.credentialForCalendarServiceSelect` | spread into select | server.ts:75, :9 (import); selects/credential.ts:3 |

## Edges at HEAD (actual A)

All `static` in the PR neighborhood — see the DI section for why that matters.

| from → to | mechanism | evidence @HEAD |
| :--- | :--- | :--- |
| `trpc.locationOptions.handler` → `srv.getLocationGroupedOptions` | unchanged | handler.ts:1, :19 |
| `features.getEventTypeById` → `srv.getLocationGroupedOptions` | unchanged | getEventTypeById.ts:3, :202 |
| `srv.getLocationGroupedOptions` → `repo.…findNonDelegationCredentialsByAppCategories` | import + **manual `new`** + call — no DI | server.ts:8 (import), :64 (`new PrismaCredentialRepository(prisma)`), :65 (call) |
| `repo.…` → `prisma.credential.table` | ctor-injected client, findMany | PrismaCredentialRepository.ts:8 (ctor), :18 (findMany); schema.prisma:308 |
| `repo.…` → `select.credentialForCalendarServiceSelect` | import + spread | :5, :28; selects/credential.ts:3 |
| `repo.…` → `lib.buildNonDelegationCredentials` | import + **unconditional** call on return | :1 (import), :38 (`return buildNonDelegationCredentials(credentials)`) |
| `srv.getLocationGroupedOptions` → `appstore.enrichUser…` | if-user branch only | server.ts:3 (import), :71 (`if (user) {`), :73 (call); else branch :83 assigns directly |
| `srv.getLocationGroupedOptions` → `appstore.getEnabledAppsFromCredentials` | call after branch merge | server.ts:10 (import), :86 (call) |

Absence evidence @HEAD: `buildNonDelegationCredentials` has **zero** matches in
`server.ts` (grep exit 1) — the dependency moved entirely into the repository.
`srv.inlineCredentialQuery` does not exist at HEAD.

## The DI edge class

- **Registration (static):** `di.CredentialModule` → `features.CredentialRepository` —
  `packages/features/di/modules/Credential.ts:1` (import), `:8` (`DI_TOKENS.CREDENTIAL_REPOSITORY`), `:14` (`classs: CredentialRepository,`).
- **A di-resolved edge:** `features.BookingAuditViewerService` → `features.CredentialRepository`, cls **di-resolved** — visible in no import statement of the consumer. Chain:
  `packages/features/booking-audit/di/BookingAuditViewerService.container.ts:13` (`container.get<BookingAuditViewerService>(…)`) →
  `packages/features/booking-audit/di/BookingAuditViewerService.module.ts:31` (`credentialRepository: credentialRepositoryModuleLoader,`) →
  `packages/features/credentials/di/CredentialRepository.module.ts:8` (token), `:15` (`classs: CredentialRepository,`) →
  `packages/features/booking-audit/lib/service/BookingAuditViewerService.ts:87` (`this.credentialRepository = deps.credentialRepository;`).
- **Twin-module ambiguity:** TWO near-identical modules bind
  `DI_TOKENS.CREDENTIAL_REPOSITORY`: `packages/features/di/modules/Credential.ts` and
  `packages/features/credentials/di/CredentialRepository.module.ts`. Grep at HEAD shows
  the former has **zero importers** — the registration consumers actually reach is the
  latter. The declared architecture itself contains a dead duplicate registration;
  $A^{*}$ has to pick one (FORMAL.md §8).
- **Absence proof for the PR's class:** `git grep -n "PrismaCredentialRepository" <HEAD> -- packages/features/di`
  → no output, exit 1. Full-tree occurrences at HEAD are exactly three:
  declaration (repo file :7), import (server.ts:8), `new` (server.ts:64). **The new
  repository is NOT DI-registered; the srv→repo edge is static.** This is why §5b's
  two models exclude DI by declared choice.

## delegationCredentialId readers

Sweep: `git grep -n "delegationCredentialId" <HEAD> -- packages/app-store packages/lib packages/trpc packages/features/eventtypes` → 98 hits, classified:

- **Type defs:** app-store/delegationCredential.ts:108,126,152; lib/buildCalEventFromBooking.ts:15; lib/delegationCredential.ts:18; lib/server/buildCredentialPayloadForCalendar.ts:6; lib/server/service/BookingWebhookFactory.ts:18.
- **Write/force sites:** lib/delegationCredential.ts:26 (the core force-null); app-store/utils.ts:70; seven calendar-app `add.ts`/adapter sites forcing null; oauth token-object writers; googlecalendar/office365 `delegatedToId` writers; buildCredentialPayloadForCalendar.ts:3,12,19; setDestinationCalendar.handler.ts:116,124.
- **Production reads (branch/select on the field):** `setDestinationCalendar.handler.ts:39` (`matchingCalendars.find((cal) => !!cal.delegationCredentialId)`), :75, :79, :88; `calendarOverlay.handler.ts:49`; `requestReschedule.handler.ts:184,195`.
- **Tests/fixtures:** ~55 hits across app tests. **Generated:** tsconfig.build.tsbuildinfo (ignore).

**Key absence:** none of the production readers sit downstream of
`getLocationGroupedOptions`. A targeted grep over `getEnabledAppsFromCredentials.ts`,
`locationOptions.handler.ts`, and all of `packages/features/eventtypes` returns zero
hits (exit 1). The field the HEAD repository unconditionally nulls is **never read on
this consumer path** — the readers live on unrelated tRPC calendar/booking paths. This
is the verified basis for §5b's "real at graph level, latent at runtime."

## Behavioral delta (the defect for D)

- **BASE:** `buildNonDelegationCredentials` applied **only in the else branch**
  (server.ts:98); the if-user branch passed **raw prisma rows** into the enrich stub
  (server.ts:87–95). server.ts:97 carries a TODO anticipating this PR's refactor.
- **HEAD:** the repository applies it **unconditionally** (PrismaCredentialRepository.ts:38),
  so the user branch now receives credentials with the three delegation fields
  force-nulled **before** enrichment. The enrich fn is an identity stub
  (delegationCredential.ts:95–99), and no reader on the path consumes the fields —
  observable output is shape-different (null keys present) but value-equivalent today.

## Caveats

- Line numbers are commit-specific; BASE and HEAD line numbers for `server.ts` differ
  (function at :14 vs :13) because the refactor removed lines above.
- `classs:` is the literal (misspelled) property name in the DI binding helper — quoted
  as-is, not a transcription error.
- The type-level cast in `lib/delegationCredential.ts:31–34` omits
  `delegationCredentialId: null` from the asserted type though the runtime forces it
  (pre-existing; first formalized as a reusable contract by this PR).
