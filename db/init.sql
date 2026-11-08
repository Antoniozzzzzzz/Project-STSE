CREATE TABLE tracks (
    id              INTEGER PRIMARY KEY,
    track_name      TEXT NOT NULL,
    artist          TEXT NOT NULL,
    year            INTEGER,
    genre           TEXT,
    topic           TEXT,
    lyrics          TEXT,
    danceability    REAL,
    loudness        REAL,
    acousticness    REAL,
    instrumentalness REAL,
    valence         REAL,
    energy          REAL
);

COPY tracks(id, track_name, artist, year, genre, topic, lyrics,
            danceability, loudness, acousticness, instrumentalness, valence, energy)
FROM '/seed/tracks.csv'
CSV HEADER;

-- Index untuk pencarian & filter
CREATE INDEX idx_tracks_genre ON tracks(genre);
CREATE INDEX idx_tracks_topic ON tracks(topic);
CREATE INDEX idx_tracks_year  ON tracks(year);
