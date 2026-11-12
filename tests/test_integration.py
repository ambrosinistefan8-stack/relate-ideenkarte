import json
import hashlib
import os
import subprocess
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'ideenkarte.py'
CLI = ROOT / 'bin' / 'relate.exe'

class RelateIntegration(unittest.TestCase):
    def test_read_commands_leave_source_database_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'ideas.rl'
            shutil.copyfile(ROOT / 'data' / 'ideas-v2.rl', db)
            for command in (['related', 'I1'], ['list'], ['graph']):
                with self.subTest(command=command):
                    before = hashlib.sha256(db.read_bytes()).hexdigest()
                    result = subprocess.run([sys.executable, str(APP), *command, '--database', str(db), '--relate', str(CLI)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(json.loads(result.stdout))
                    self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(), before, f'{command[0]} changed the source database')

    def test_persistent_graph_survives_reopen_and_finds_shared_theme(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'ideas.rl'
            env = dict(os.environ, RELATE_TELEMETRY='0')
            created = subprocess.run([sys.executable, str(APP), 'seed', '--database', str(db), '--relate', str(CLI)], capture_output=True, text=True, env=env)
            self.assertEqual(created.returncode, 0, created.stderr)
            self.assertTrue(db.exists())
            queried = subprocess.run([sys.executable, str(APP), 'related', 'I1', '--database', str(db), '--relate', str(CLI)], capture_output=True, text=True, env=env)
            self.assertEqual(queried.returncode, 0, queried.stderr)
            rows = json.loads(queried.stdout)
            self.assertTrue(any(row['idea_id'] == 'I2' and row['theme'] == 'Stadtgruen' for row in rows), rows)
            self.assertFalse(any(row['idea_id'] == 'I1' for row in rows))

    def test_graph_returns_real_nodes_and_relationships(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'ideas.rl'
            common = ['--database', str(db), '--relate', str(CLI)]
            seeded = subprocess.run([sys.executable, str(APP), 'seed', *common], capture_output=True, text=True)
            self.assertEqual(seeded.returncode, 0, seeded.stderr)
            graph = subprocess.run([sys.executable, str(APP), 'graph', *common], capture_output=True, text=True)
            self.assertEqual(graph.returncode, 0, graph.stderr)
            data = json.loads(graph.stdout)
            self.assertEqual(len(data['ideas']), 4)
            self.assertEqual(len(data['themes']), 3)
            self.assertIn({'idea_id': 'I1', 'theme': 'Stadtgruen'}, data['links'])
            self.assertEqual(len(data['links']), 6)
            self.assertTrue(any(x['id'] == 'D1' for x in data['documents']))
            self.assertTrue(any(x['id'] == 'A1' for x in data['agents']))
            self.assertTrue(any(x['id'] == 'T1' for x in data['tasks']))
            self.assertIn({'source': 'D1', 'type': 'DESCRIBES', 'target': 'I1'}, data['relations'])
            self.assertIn({'source': 'T1', 'type': 'SUPPORTS', 'target': 'I1'}, data['relations'])
            self.assertIn({'source': 'A1', 'type': 'WORKS_ON', 'target': 'T1'}, data['relations'])

if __name__ == '__main__':
    unittest.main()
