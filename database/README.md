# Database — IBM Db2 Community Edition 12.1.5

Db2 is the mandatory primary store. AEGIS does not fall back to SQLite, PostgreSQL, or
an in-memory database. When Db2 is unavailable the API returns `503` and the UI shows
a degraded status.

## Expected local configuration

```text
Host:     localhost
Port:     50000
Database: TESTDB
Username: db2inst1
Password: from DB2_PASSWORD in .env
Schema:   AEGIS
```

## Provisioning

Use an existing local Db2 instance, or start the official container:

```bash
export DB2_PASSWORD='choose-a-local-password'
podman run -d --name aegis-db2 --platform linux/amd64 --privileged=true \
  -p 50000:50000 \
  -e LICENSE=accept \
  -e DB2INST1_PASSWORD="$DB2_PASSWORD" \
  -e DBNAME=TESTDB \
  -e ARCHIVE_LOGS=false \
  icr.io/db2_community/db2:12.1.5.0
```

Wait for `(*) Setup has completed.` in `podman logs -f aegis-db2`. On Apple Silicon
the amd64 image runs under emulation and can take several minutes. The container needs
several GB of free memory.

## Initialize

```bash
make db-init
# or
python database/init_db.py --stats
```

`init_db.py`:

- validates the schema name;
- creates schema `AEGIS` if missing;
- applies `database/schema.sql` idempotently (ignores already-exists SQLCODEs);
- commits DDL explicitly;
- prints row counts and confirms all six tables exist.

Reset a local schema:

```bash
python database/init_db.py --drop --stats
```

`--drop` deletes AEGIS tables and is intended for local development only.

## Seed

```bash
make db-seed
```

This inserts only the clearly labelled synthetic evidence document. It does not insert
verification results or expected classifications.

## Schema

See [`schema.sql`](schema.sql) for exact Db2 types. Six tables:

1. `DOCUMENTS` — evidence metadata and SHA-256 content hash.
2. `PASSAGES` — chunked passage text with page and index.
3. `VERIFICATION_SESSIONS` — submitted text, provider/model label, status, errors.
4. `CLAIMS` — atomic claims and source spans.
5. `VERIFICATION_RESULTS` — constrained classification, explanation, limitations, method.
6. `EVIDENCE_LINKS` — result ↔ passage links with retrieval score.

Foreign keys enforce referential integrity with cascading deletes. Indexes cover
document passage lookup, session claims, evidence links, and recent ordering.

## Transactions and cleanup

- Every repository operation uses an explicit connection context.
- Multi-row writes (claims, results, links, final status) run in one transaction.
- Failures roll back and mark the session `FAILED` when possible.
- Statements are prepared and freed; connections are always closed.
- No raw Db2 exception or DSN is returned to clients.

## Platform note: ibm_db 3.3.0 on macOS arm64

`ibm_db.exec_immediate(conn, sql, params)` with parameter markers can segfault on this
platform. AEGIS uses `ibm_db.prepare` + `ibm_db.bind_param` + `ibm_db.execute` and
explicitly frees statements. SQL remains parameterized. `init_db.py` uses literal SQL
only for validated identifiers and DDL, and uses prepared statements everywhere else
in the application.

## Troubleshooting

- **SQLCODE -286 / table space** — the database does not have a usable temporary or
  user table space; recreate TESTDB with the container defaults.
- **Connection refused** — container not finished starting; check `podman logs`.
- **Authentication failed** — `DB2_PASSWORD` must match `DB2INST1_PASSWORD` used when
  the container was created. Changing `.env` does not change an existing instance.
- **Missing tables** — run `make db-init`.
- **Schema appears empty** — the API sets `CURRENT SCHEMA AEGIS`; inspect with
  `SELECT * FROM AEGIS.DOCUMENTS`.
