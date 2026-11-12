"""Local, fictional idea graph using the official Relate CLI."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = """CREATE
(i1:Idea {id:'I1', title:'Gruene Haltestelle', description:'Warteorte mit Pflanzen und Schatten'}),
(i2:Idea {id:'I2', title:'Nachbarschaftsgarten', description:'Gemeinsam kleine Flaechen begruenen'}),
(i3:Idea {id:'I3', title:'Reparaturtreff', description:'Werkzeuge und Reparaturwissen teilen'}),
(i4:Idea {id:'I4', title:'Schattenkarte', description:'Kuehle Wege durch die Stadt sichtbar machen'}),
(d1:Document {id:'D1', title:'Skizze gruene Haltestelle'}),
(d2:Document {id:'D2', title:'Notizen Gemeinschaftsgarten'}),
(task1:Task {id:'T1', title:'Standort fuer Haltestelle pruefen'}),
(task2:Task {id:'T2', title:'Pflanzbeete planen'}),
(a1:Agent {id:'A1', name:'Ideenhelfer'}),
(a2:Agent {id:'A2', name:'Planungshelfer'}),
(t1:Theme {name:'Stadtgruen'}), (t2:Theme {name:'Gemeinschaft'}), (t3:Theme {name:'Klima'}),
(i1)-[:HAS_THEME]->(t1), (i1)-[:HAS_THEME]->(t3),
(i2)-[:HAS_THEME]->(t1), (i2)-[:HAS_THEME]->(t2),
(i3)-[:HAS_THEME]->(t2), (i4)-[:HAS_THEME]->(t3),
(d1)-[:DESCRIBES]->(i1), (d2)-[:DESCRIBES]->(i2),
(task1)-[:SUPPORTS]->(i1), (task2)-[:SUPPORTS]->(i2),
(a1)-[:WORKS_ON]->(task1), (a2)-[:WORKS_ON]->(task2)"""


def run_query(cli, database, query, params=()):
    env = os.environ.copy()
    env['RELATE_TELEMETRY'] = '0'
    command = [str(cli), '--jsonl', '-d', str(database)]
    for param in params:
        command.extend(['--param', param])
    result = subprocess.run(command + [query], capture_output=True, text=True, encoding='utf-8', env=env, timeout=30)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['seed', 'related', 'list', 'graph'])
    parser.add_argument('idea_id', nargs='?')
    parser.add_argument('--database', type=Path, default=ROOT / 'data' / 'ideas-v2.rl')
    parser.add_argument('--relate', type=Path, default=ROOT / 'bin' / 'relate.exe')
    args = parser.parse_args()
    if not args.relate.is_file():
        parser.error('Relate executable not found: ' + str(args.relate))
    if args.command == 'seed':
        if args.database.exists():
            parser.error('Refusing to overwrite an existing store: ' + str(args.database))
        args.database.parent.mkdir(parents=True, exist_ok=True)
        run_query(args.relate, args.database, SEED)
        print('Created fictional graph: ' + str(args.database))
    else:
        if not args.database.exists():
            parser.error('Store not found; run seed first: ' + str(args.database))
        # Relate may update its store even for MATCH queries. Execute the whole
        # read operation against one disposable snapshot, preserving the source.
        with tempfile.TemporaryDirectory(prefix='ideenkarte-read-') as temp_dir:
            snapshot = Path(temp_dir) / 'ideas.rl'
            shutil.copyfile(args.database, snapshot)
            rows = read_graph(args, parser, snapshot)
        print(json.dumps(rows, ensure_ascii=False, indent=2))


def read_graph(args, parser, snapshot):
    if args.command == 'related':
        if not args.idea_id:
            parser.error('related requires an idea id')
        q = ('MATCH (source:Idea {id:$id})-[:HAS_THEME]->(theme:Theme)<-[:HAS_THEME]-(other:Idea) '
             'WHERE other.id <> source.id '
             'RETURN other.id AS idea_id, other.title AS title, theme.name AS theme ORDER BY idea_id, theme')
        rows = run_query(args.relate, snapshot, q, [f'id={args.idea_id}'])
    elif args.command == 'graph':
        rows = {
            'ideas': run_query(args.relate, snapshot, 'MATCH (i:Idea) RETURN i.id AS id, i.title AS title, i.description AS description ORDER BY id'),
            'themes': run_query(args.relate, snapshot, 'MATCH (t:Theme) RETURN t.name AS name ORDER BY name'),
            'links': run_query(args.relate, snapshot, 'MATCH (i:Idea)-[:HAS_THEME]->(t:Theme) RETURN i.id AS idea_id, t.name AS theme ORDER BY idea_id, theme'),
            'documents': run_query(args.relate, snapshot, 'MATCH (n:Document) RETURN n.id AS id, n.title AS title ORDER BY id'),
            'tasks': run_query(args.relate, snapshot, 'MATCH (n:Task) RETURN n.id AS id, n.title AS title ORDER BY id'),
            'agents': run_query(args.relate, snapshot, 'MATCH (n:Agent) RETURN n.id AS id, n.name AS name ORDER BY id'),
            'relations': run_query(args.relate, snapshot, 'MATCH (a)-[r]->(b) WHERE a.id IS NOT NULL AND b.id IS NOT NULL RETURN a.id AS source, type(r) AS type, b.id AS target ORDER BY source, target'),
        }
    else:
        rows = run_query(args.relate, snapshot, 'MATCH (i:Idea) RETURN i.id AS idea_id, i.title AS title, i.description AS description ORDER BY idea_id')
    return rows

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
