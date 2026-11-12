# Ideas Map — connected context with Relate

Ideas Map is a small, local, read-only visual explorer for a fictional graph. It connects ideas to themes, documents and tasks, and represents fictional agents as graph nodes. A selected idea can be explored through its relationships; related ideas share a theme. The agents are illustrative records, not autonomous programs.

## How it uses Relate

The app queries the actual Relate graph using the official Relate CLI; the UI has no fallback dataset. The storage mode is a persistent single file, `data/ideas-v2.rl`, so the same graph can be reopened and inspected. The data contains no real people or private information. Ideas, themes, documents, tasks and agents are nodes; `HAS_THEME`, `DESCRIBES`, `SUPPORTS` and `WORKS_ON` are graph relationships. The `related` command traverses `Idea -> Theme <- Idea` and reports the common theme.

## Requirements

- Windows x64, Python 3 and Node.js 18 or later. The local check used Python 3.15.2 and Relate 1.0.1.
- The official Relate 1.0.1 Windows binary. This repository does not include the executable. Relate is an experimental Neo4j Labs product under Apache-2.0; see [Relate](https://github.com/relatedb/relate).
- No account, paid service, server deployment or API key is required for this local example.

## Setup on Windows PowerShell

From the project directory, download the binary from the official release and verify it before use:

```powershell
New-Item -ItemType Directory -Force bin | Out-Null
Invoke-WebRequest 'https://github.com/relatedb/relate/releases/download/v1.0.1/relate-windows-amd64.exe' -OutFile 'bin/relate.exe'
Get-FileHash 'bin/relate.exe' -Algorithm SHA256
```

The hash must be `08F3E1BA00737C4600B73605AD8FA576B5EEE7706BB03DD33E05D9276836AE4A`. The upstream [release](https://github.com/relatedb/relate/releases/tag/v1.0.1) publishes the executable and checksum manifest. Do not run the binary if its hash does not match. No dependency installation is needed for the application.

Start the local server:

```powershell
node server.js
```

Open http://127.0.0.1:5187 and stop the server with `Ctrl+C`. It listens on loopback only. If the port is occupied, set `$env:PORT='5188'` before starting. On Windows the server selects Python via `py -3`; set `IDEENKARTE_PYTHON` to the full Python executable path if needed. The server invokes fixed commands without a shell and only exposes read-only graph data.

## Inspect or create a separate store

```powershell
python ideenkarte.py graph
python ideenkarte.py list
python ideenkarte.py related I1
python ideenkarte.py seed --database data/new-ideas.rl
```

`graph` produces JSON directly from Relate. `related I1` finds I2 via Stadtgruen and I4 via Klima. Because the Relate CLI can update a store even for a read query, each read command copies the source database into a temporary directory, queries that snapshot and cleans it up afterwards. This preserves the source file and keeps all queries in one `graph` call on the same snapshot. The seed command writes a new store and refuses to overwrite an existing one. The included graph is ready to inspect; seeding is optional.

## Verify

```powershell
python -m unittest discover -s tests -v
```

The integration tests create isolated temporary stores, reopen them in another process, check graph relationships and confirm the returned nodes. They require the binary at `bin/relate.exe`. For a manual check, load the UI and confirm the graph appears, select an idea and search for a node. Missing Relate or store data produces an error rather than sample results.

## Privacy, telemetry and attribution

Only synthetic demonstration data is supplied. Every CLI subprocess is started with `RELATE_TELEMETRY=0`; upstream documents that CLI telemetry is otherwise enabled by default. The app does not invoke a hosted AI model or a paid API. Codex AI assistance was used to develop and document this project; the resulting code and data must be reviewed and the test results verified by its submitter. Relate and Neo4j are their respective owners' marks.

## Demo and license

`demo.mp4` is an 87-second silent captioned walkthrough using screenshots from the running local app. The project source is available under the MIT License; Relate itself is distributed separately under Apache-2.0.
