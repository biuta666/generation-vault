"""M2: SQLite 存储层 — Generation 入库/出库

规则:
- 只做 insert / select / update
- 不写搜索逻辑 (M3)
- 不写 UI (M4)
- 不用 ORM，原生 sqlite3
"""
import sqlite3, json, os
from typing import Optional, List
from pathlib import Path

from parser.base import Generation, LoraRef

SCHEMA_VERSION = 1


class Database:
    """Generation 存储"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    # ---- Schema ----

    def _migrate(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS _meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS generations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path    TEXT NOT NULL,
                image_hash    TEXT,
                prompt        TEXT DEFAULT '',
                negative      TEXT DEFAULT '',
                model_name    TEXT DEFAULT '',
                model_hash    TEXT DEFAULT '',
                lora_json     TEXT DEFAULT '[]',
                seed          INTEGER DEFAULT -1,
                cfg           REAL DEFAULT 0.0,
                sampler       TEXT DEFAULT '',
                steps         INTEGER DEFAULT 0,
                width         INTEGER DEFAULT 0,
                height        INTEGER DEFAULT 0,
                workflow_json TEXT DEFAULT '',
                source_tool   TEXT DEFAULT '',
                parser_name   TEXT DEFAULT '',
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- FTS5 表只建不写搜索逻辑(M3)
            CREATE VIRTUAL TABLE IF NOT EXISTS generations_fts
                USING fts5(prompt, negative, model_name, lora_json,
                           content='generations', content_rowid='id');

            -- Triggers: insert/update/delete 自动同步 FTS
            CREATE TRIGGER IF NOT EXISTS gens_ai AFTER INSERT ON generations BEGIN
                INSERT INTO generations_fts(rowid, prompt, negative, model_name, lora_json)
                VALUES (new.id, new.prompt, new.negative, new.model_name, new.lora_json);
            END;

            CREATE TRIGGER IF NOT EXISTS gens_ad AFTER DELETE ON generations BEGIN
                INSERT INTO generations_fts(generations_fts, rowid, prompt, negative, model_name, lora_json)
                VALUES('delete', old.id, old.prompt, old.negative, old.model_name, old.lora_json);
            END;

            CREATE TRIGGER IF NOT EXISTS gens_au AFTER UPDATE ON generations BEGIN
                INSERT INTO generations_fts(generations_fts, rowid, prompt, negative, model_name, lora_json)
                VALUES('delete', old.id, old.prompt, old.negative, old.model_name, old.lora_json);
                INSERT INTO generations_fts(rowid, prompt, negative, model_name, lora_json)
                VALUES (new.id, new.prompt, new.negative, new.model_name, new.lora_json);
            END;
        """)
        self.conn.execute(
            "INSERT OR IGNORE INTO _meta(key, value) VALUES(?, ?)",
            ("schema_version", str(SCHEMA_VERSION))
        )
        self.conn.commit()

    # ---- CRUD ----

    def insert(self, gen: Generation) -> int:
        """写入一条 Generation，返回 ID"""
        cursor = self.conn.execute(
            """INSERT INTO generations
               (image_path, image_hash, prompt, negative, model_name, model_hash,
                lora_json, seed, cfg, sampler, steps, width, height,
                workflow_json, source_tool, parser_name)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                gen.image_path,
                gen.image_hash if hasattr(gen, 'image_hash') else '',
                gen.prompt,
                gen.negative,
                gen.model_name,
                gen.model_hash,
                json.dumps([{
                    'name': l.name if hasattr(l, 'name') else l.get('name', ''),
                    'weight': l.weight if hasattr(l, 'weight') else l.get('weight', 0)
                } for l in gen.loras], ensure_ascii=False),
                gen.seed,
                gen.cfg,
                gen.sampler,
                gen.steps,
                gen.width,
                gen.height,
                gen.workflow_json,
                gen.source_tool,
                gen.parser_name,
            )
        )
        self.conn.commit()
        return cursor.lastrowid

    def get(self, gen_id: int) -> Optional[Generation]:
        """按 ID 读取"""
        row = self.conn.execute(
            "SELECT * FROM generations WHERE id = ?", (gen_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_gen(row)

    def get_all(self, limit: int = 100) -> List[Generation]:
        """读取最近 N 条"""
        rows = self.conn.execute(
            "SELECT * FROM generations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_gen(r) for r in rows]

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM generations").fetchone()[0]

    # ---- Helpers ----

    def _row_to_gen(self, row: sqlite3.Row) -> Generation:
        loras_raw = json.loads(row['lora_json'] or '[]')
        loras = [LoraRef(name=l['name'], weight=l['weight']) for l in loras_raw]
        return Generation(
            image_path=row['image_path'],
            prompt=row['prompt'],
            negative=row['negative'],
            model_name=row['model_name'],
            model_hash=row['model_hash'],
            loras=loras,
            seed=row['seed'],
            cfg=row['cfg'],
            sampler=row['sampler'],
            steps=row['steps'],
            width=row['width'],
            height=row['height'],
            workflow_json=row['workflow_json'],
            source_tool=row['source_tool'],
            parser_name=row['parser_name'],
        )

    def close(self):
        self.conn.close()

    # ---- M3: Query (仅 FTS5 关键字搜索) ----

    def query(self, keyword: str, limit: int = 20) -> List[Generation]:
        """FTS5 全文搜索 prompt/negative/model_name/lora_json"""
        rows = self.conn.execute(
            """SELECT * FROM generations
               WHERE id IN (SELECT rowid FROM generations_fts WHERE generations_fts MATCH ?)
               ORDER BY id DESC LIMIT ?""",
            (keyword, limit)
        ).fetchall()
        return [self._row_to_gen(r) for r in rows]

    def query_by_model(self, model_name: str, limit: int = 20) -> List[Generation]:
        rows = self.conn.execute(
            "SELECT * FROM generations WHERE model_name LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{model_name}%", limit)
        ).fetchall()
        return [self._row_to_gen(r) for r in rows]

    def query_by_lora(self, lora_name: str, limit: int = 20) -> List[Generation]:
        rows = self.conn.execute(
            "SELECT * FROM generations WHERE lora_json LIKE ? ORDER BY id DESC LIMIT ?",
            (f"%{lora_name}%", limit)
        ).fetchall()
        return [self._row_to_gen(r) for r in rows]

    def query_by_seed(self, seed: int, limit: int = 20) -> List[Generation]:
        rows = self.conn.execute(
            "SELECT * FROM generations WHERE seed = ? ORDER BY id DESC LIMIT ?",
            (seed, limit)
        ).fetchall()
        return [self._row_to_gen(r) for r in rows]
