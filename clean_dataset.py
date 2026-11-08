#!/usr/bin/env python3
"""Bersihkan dataset Kaggle 'Music Dataset 1950-2019' menjadi tracks.csv."""
import pandas as pd
import os

# ---- Konfigurasi ----
INPUT  = "tcc_ceds_music.csv"          # file asli dari Kaggle
OUTPUT = os.path.join("db", "tracks.csv")

# ---- Baca & cek kolom asli ----
df = pd.read_csv(INPUT)
print("=== Kolom asli CSV ===")
print(df.columns.tolist())
print(f"Jumlah baris awal: {len(df):,}")

# ---- Rename kolom sesuai skema ----
df = df.rename(columns={
    "artist_name": "artist",
    "release_date": "year",
})

# ---- Pilih kolom yang dibutuhkan ----
COLS = [
    "track_name", "artist", "year", "genre", "topic",
    "lyrics", "danceability", "loudness", "acousticness",
    "instrumentalness", "valence", "energy",
]
df = df[COLS]

# ---- Bersihkan ----
before = len(df)
df = df.drop_duplicates(subset=["track_name", "artist"])
print(f"Drop duplikat: {before - len(df):,} baris dihapus")

before = len(df)
df = df.dropna()
print(f"Drop baris kosong: {before - len(df):,} baris dihapus")

# ---- Tipe data ----
df["year"] = df["year"].astype(int)

# Hapus null bytes di lyrics (bisa rusak saat COPY PostgreSQL)
df["lyrics"] = df["lyrics"].str.replace("\x00", "", regex=False)

# ---- Tambah id (1-based) ----
df.insert(0, "id", range(1, len(df) + 1))

# ---- Simpan ----
os.makedirs("db", exist_ok=True)
df.to_csv(OUTPUT, index=False)
print(f"\n✅ Hasil: {len(df):,} lagu disimpan ke {OUTPUT}")
