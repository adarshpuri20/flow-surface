# Deployment sync

Some projects implement in one place and commit from another — code is edited on a remote
host for access to real infrastructure, then synced back to the local checkout for commit.

This is a real pattern with a real failure mode: files edited remotely and never synced
are lost on the next pull, silently.

## Sync sweep

Before finalising a phase, reconcile the two locations:

1. From the conductor state's accumulated `files_modified`, list every file the phase
   touched.
2. For each, compare the remote and local copies (checksum, not timestamp — timestamps lie
   after a checkout).
3. Copy back anything that differs, or is missing locally.
4. Report the sweep: files compared, files copied, files skipped and why.
5. Only then stage and commit.

Configure the transport in `.flow-surface.json` under `remote`. When `remote.mode` is
`local`, skip this step entirely rather than failing.

## Guard rails worth keeping

- **Never push from the build host.** Commit and push from one place only. Two push
  origins produce divergent history that is tedious to unpick.
- **Pulls are fine**; pushes are not.
- **Kill the service before running migrations**, and terminate open datastore sessions
  first, or the migration blocks on locks and leaves the schema half-applied.
