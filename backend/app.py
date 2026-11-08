"""Music Library REST API – Flask + psycopg2."""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Database helper
# ---------------------------------------------------------------------------

def get_conn():
    return psycopg2.connect(
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
    )

# ---------------------------------------------------------------------------
# GET /api/tracks  –  list dengan pagination, search, filter, sorting
# ---------------------------------------------------------------------------

SORT_MAP = {
    "title":        "track_name ASC",
    "newest":       "year DESC",
    "oldest":       "year ASC",
    "energy":       "energy DESC",
    "danceability": "danceability DESC",
}

@app.route("/api/tracks")
def list_tracks():
    # --- params ---
    page  = max(1, request.args.get("page", 1, type=int))
    limit = min(max(1, request.args.get("limit", 20, type=int)), 100)
    q     = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    topic = request.args.get("topic", "").strip()
    year_from = request.args.get("year_from", None, type=int)
    year_to   = request.args.get("year_to",   None, type=int)
    sort_key  = request.args.get("sort", "title").strip()

    # --- bangun WHERE (parameterized) ---
    clauses = []
    params  = []

    if q:
        clauses.append("(track_name ILIKE %s OR artist ILIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])
    if genre:
        clauses.append("genre = %s")
        params.append(genre)
    if topic:
        clauses.append("topic = %s")
        params.append(topic)
    if year_from is not None:
        clauses.append("year >= %s")
        params.append(year_from)
    if year_to is not None:
        clauses.append("year <= %s")
        params.append(year_to)

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    # --- ORDER BY (hanya dari map, bukan user input) + tie-breaker ---
    order_sql = SORT_MAP.get(sort_key, "track_name ASC") + ", id ASC"

    offset = (page - 1) * limit

    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # hitung total
            cur.execute(f"SELECT COUNT(*) AS total FROM tracks {where_sql}", params)
            total = cur.fetchone()["total"]

            # ambil data (tanpa lyrics di list)
            cur.execute(
                f"""SELECT id, track_name, artist, year, genre, topic,
                           danceability, loudness, acousticness,
                           instrumentalness, valence, energy
                    FROM tracks {where_sql}
                    ORDER BY {order_sql}
                    LIMIT %s OFFSET %s""",
                params + [limit, offset],
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify({"data": rows, "page": page, "limit": limit, "total": total})

# ---------------------------------------------------------------------------
# GET /api/tracks/<id>  –  detail lengkap (termasuk lyrics)
# ---------------------------------------------------------------------------

@app.route("/api/tracks/<int:track_id>")
def track_detail(track_id):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tracks WHERE id = %s", (track_id,))
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "Track not found"}), 404
    return jsonify(row)

# ---------------------------------------------------------------------------
# GET /api/filters  –  opsi untuk dropdown
# ---------------------------------------------------------------------------

@app.route("/api/filters")
def filters():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT genre FROM tracks "
                "WHERE genre IS NOT NULL ORDER BY genre"
            )
            genres = [r[0] for r in cur.fetchall()]

            cur.execute(
                "SELECT DISTINCT topic FROM tracks "
                "WHERE topic IS NOT NULL ORDER BY topic"
            )
            topics = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT MIN(year), MAX(year) FROM tracks")
            yr = cur.fetchone()
    finally:
        conn.close()

    return jsonify({
        "genres":   genres,
        "topics":   topics,
        "year_min": yr[0],
        "year_max": yr[1],
    })

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
