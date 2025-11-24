import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path
from io import BytesIO

DB_PATH = Path("songs.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS songs (
        title TEXT NOT NULL,
        singer TEXT NOT NULL,
        year INTEGER NOT NULL,
        genre TEXT,
        composer TEXT,
        album TEXT,
        PRIMARY KEY(title, singer, year)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS playlists (
        playlist_name TEXT NOT NULL,
        song_title TEXT NOT NULL,
        singer TEXT,
        year INTEGER,
        genre TEXT,
        PRIMARY KEY(playlist_name, song_title)
    )""")
    conn.commit()
    cur.execute("SELECT count(1) FROM songs")
    if cur.fetchone()[0] == 0:
        bulk_insert(cur)
        conn.commit()
    conn.close()

def bulk_insert(cur):
    songs_data = [
        ("Bulleeya", "Pritam", 2016, "Rock", "Pritam", "Ae Dil Hai Mushkil"),
        ("Ae Dil Hai Mushkil", "Arijit Singh", 2016, "Romance", "Pritam", "Ae Dil Hai Mushkil"),
        ("Sunn Raha Hai (Male)", "Ankit Tiwari", 2013, "Romance", "Ankit Tiwari", "Aashiqui 2"),
        ("Kabhi Jo Baadal Barse", "Arijit Singh", 2013, "Romance", "Sharib-Toshi", "Jackpot"),
        ("Tum Hi Ho", "Arijit Singh", 2013, "Romance", "Mithoon", "Aashiqui 2"),
        ("Chahun Main Ya Naa", "Palak Muchhal", 2013, "Romance", "Jeet Gannguli", "Aashiqui 2"),
        ("Galliyan", "Ankit Tiwari", 2014, "Romance", "Ankit Tiwari", "Ek Villain"),
        ("Tum Hi Ho Bandhu", "Neeraj Shridhar", 2012, "Pop", "Pritam", "Cocktail"),
        ("I'll Be Waiting (Kabhi Jo Baadal)", "Arjun", 2013, "Fusion", "Arjun", "Single"),
        ("Kun Faya Kun", "A.R. Rahman", 2011, "Sufi", "A.R. Rahman", "Rockstar"),
        ("Kar Har Maidaan Fateh", "Sukhwinder Singh", 2018, "Motivational", "Vikram Montrose", "Sanju"),
        ("Bhaag D.K. Bose", "Ram Sampath", 2011, "Rock", "Ram Sampath", "Delhi Belly"),
        ("Gulabi Aankhen", "Sanam", 2015, "Romantic Pop", "Sanam", "Sanam Singles"),
        ("Channa Mereya", "Arijit Singh", 2016, "Romance", "Pritam", "Ae Dil Hai Mushkil"),
        ("Agar Tum Saath Ho", "Alka Yagnik", 2015, "Romance", "A.R. Rahman", "Tamasha"),
        ("Hawayein", "Arijit Singh", 2017, "Romance", "Pritam", "Jab Harry Met Sejal"),
        ("Kabira", "Tochi Raina", 2013, "Romance", "Pritam", "Yeh Jawaani Hai Deewani"),
        ("Ek Vaari Aa", "Arijit Singh", 2017, "Romance", "Pritam", "Raabta"),
        ("Ilahi", "Arijit Singh", 2013, "Adventure", "Pritam", "Yeh Jawaani Hai Deewani"),
        ("Subhanallah", "Sreerama Chandra", 2013, "Romance", "Vishal-Shekhar", "Yeh Jawaani Hai Deewani"),
        ("Mataragashti", "Mohit Chauhan", 2015, "Romantic Pop", "A.R. Rahman", "Tamasha"),
        ("Sooraj Dooba Hain", "Arijit Singh", 2015, "Party", "Amaal Mallik", "Roy"),
        ("Dil Dhadakne Do", "Joi Barua", 2015, "Pop", "Shankar-Ehsaan-Loy", "Zindagi Na Milegi Dobara"),
        ("Tum Se Hi", "Mohit Chauhan", 2007, "Romance", "Pritam", "Jab We Met"),
        ("Tera Hone Laga Hoon", "Atif Aslam", 2009, "Romance", "Pritam", "Ajab Prem Ki Ghazab Kahani"),
        ("Pehli Nazar Mein", "Atif Aslam", 2008, "Romance", "Pritam", "Race"),
        ("Khairiyat", "Arijit Singh", 2019, "Romance", "Pritam", "Chhichhore"),
        ("Hamari Adhuri Kahani", "Jeet Gannguli", 2015, "Romance", "Jeet Gannguli", "Hamari Adhuri Kahani"),
        ("Main Agar Kahoon", "Sonu Nigam", 2007, "Romance", "Vishal-Shekhar", "Om Shanti Om"),
        ("Main Hoon Na", "Sonu Nigam", 2004, "Romance", "Anu Malik", "Main Hoon Na"),
        ("Hasi (Male Version)", "Ami Mishra", 2015, "Romance", "Ami Mishra", "Hamari Adhuri Kahani"),
        ("Tujhe Bhula Diya", "Mohit Chauhan", 2010, "Romance", "Vishal-Shekhar", "Anjaana Anjaani"),
        ("Bekhayali", "Arijit Singh", 2019, "Romance", "Sachet-Parampara", "Kabir Singh"),
        ("Sanam Re", "Arijit Singh", 2016, "Romance", "Mithoon", "Sanam Re"),
        ("Jab Tak", "Armaan Malik", 2016, "Romance", "Amaal Malik", "M.S. Dhoni: The Untold Story"),
        ("Ishq Wala Love", "Vishal-Shekhar", 2012, "Romance", "Vishal-Shekhar", "Student of the Year"),
        ("Tu Jaane Na", "Atif Aslam", 2009, "Romance", "Pritam", "Ajab Prem Ki Ghazab Kahani"),
        ("Mann Mera", "Gajendra Verma", 2012, "Pop", "Gajendra Verma", "Table No. 21"),
        ("Shayad", "Pritam", 2020, "Romance", "Pritam", "Love Aaj Kal"),
        ("Tum Jo Aaye", "Tulsi Kumar", 2010, "Romance", "Pritam", "Once Upon A Time In Mumbaai"),
        ("Ye Tune Kya Kiya", "Javed Bashir", 2014, "Romance", "Pritam", "Once Upon A Time In Mumbaai Dobara"),
        ("Pee Loon", "Mohan Kanan", 2010, "Romance", "Pritam", "Once Upon A Time In Mumbaai"),
        ("Zara Sa", "Javed Ali", 2008, "Romance", "Pritam", "Jannat"),
        ("Chhod Diya", "Arijit Singh", 2019, "Romance", "Amaal Mallik", "Baazaar"),
        ("Pal", "Arijit Singh", 2018, "Romance", "Javed-Mohsin", "Jalebi"),
        ("Jeene Ke Hain Chaar Din", "Sonu Nigam", 2004, "Comedy", "Sajid-Wajid", "Mujhse Shaadi Karogi"),
        ("Jeene Laga Hoon", "Atif Aslam", 2013, "Romance", "Sachin-Jigar", "Ramaiya Vastavaiya"),
        ("Dil Ibaadat", "KK", 2009, "Romance", "Pritam", "Tum Mile"),
        ("Mere Rashke Qamar", "Rahat Fateh Ali Khan", 2017, "Sufi", "Nusrat Fateh Ali Khan", "Baadshaho"),
        ("Allah Waariyan", "Shafqat Amanat Ali", 2014, "Romance", "Raju Singh", "Yaariyan"),
        ("Hasi Ban Gaye", "Ami Mishra", 2015, "Romance", "Ami Mishra", "Hamari Adhuri Kahani"),
        ("Gerua", "Arijit Singh", 2015, "Romance", "Pritam", "Dilwale"),
        ("Ghunghroo", "Arijit Singh", 2019, "Party", "Vishal-Shekhar", "War"),
        ("Phir Bhi Tumko Chaahunga", "Arijit Singh", 2017, "Romance", "Mithoon", "Half Girlfriend"),
        ("Paniyon Sa", "Atif Aslam", 2018, "Romance", "Rochak Kohli", "Satyameva Jayate"),
        ("Kamli", "Sunidhi Chauhan", 2013, "Dance", "Pritam", "Dhoom 3"),
        ("Aankh Marey", "Neha Kakkar", 2018, "Party", "Tanishk Bagchi", "Simmba"),
        ("Tera Ban Jaunga", "Tulsi Kumar", 2019, "Romance", "Gulshan Kumar", "Kabir Singh"),
        ("Dil Diyan Gallan", "Atif Aslam", 2017, "Romance", "Rahat Fateh Ali Khan", "Tiger Zinda Hai"),
        ("Jaane Tu Ya Jaane Na", "Rashid Ali", 2008, "Pop", "A.R. Rahman", "Jaane Tu Ya Jaane Na"),
        ("Tujhe Kitna Chahne Lage", "Arijit Singh", 2019, "Romance", "Mithoon", "Kabir Singh"),
        ("Kesariya", "Arijit Singh", 2022, "Romance", "Pritam", "Brahmastra: Part One – Shiva"),
        ("Naata Naatu", "Rahul Sipligunj", 2021, "Dance", "M.M. Keeravani", "RRR"),
        ("Apna Bana Le", "Arijit Singh", 2022, "Romance", "Sachin-Jigar", "Bhediya"),
        ("Raabta", "Arijit Singh", 2020, "Romance", "A.R. Rahman", "Shikara"),
        ("Jhoome Jo Pathaan", "Arijit Singh", 2023, "Party", "Vishal-Shekhar", "Pathaan"),
        ("Tere Sang Yaara", "Atif Aslam", 2016, "Romance", "Arko", "Rustom"),
        ("Kalank Title Track", "Arijit Singh", 2019, "Romance", "Pritam", "Kalank"),
        ("Banjara", "Mohammed Irfan", 2014, "Romance", "Mithoon", "Ek Villain"),
        ("Dil Chahta Hai", "Shankar Mahadevan", 2001, "Pop", "Shankar-Ehsaan-Loy", "Dil Chahta Hai"),
        ("Makhna", "Asees Kaur", 2018, "Party", "Tanishk Bagchi", "Drive"),
        ("Lehra Do", "Arijit Singh", 2021, "Motivational", "Pritam", "83"),
        ("Qaafirana", "Arijit Singh", 2018, "Romance", "A.R. Rahman", "Kedarnath"),
        ("Mast Magan", "Arijit Singh", 2014, "Romance", "Shankar-Ehsaan-Loy", "2 States"),
        ("Gallan Goodiyan", "Shankar Mahadevan", 2015, "Party", "Shankar-Ehsaan-Loy", "Dil Dhadakne Do"),
        ("Mehram", "Darshan Raval", 2020, "Romance", "Pritam", "Love Aaj Kal"),
        ("Desi Girl", "Shankar Mahadevan", 2008, "Pop", "Vishal-Shekhar", "Dostana"),
        ("Shubhaarambh", "Shruti Pathak", 2013, "Folk", "Amit Trivedi", "Kai Po Che"),
        ("Phir Se Ud Chala", "Mohit Chauhan", 2011, "Adventure", "A.R. Rahman", "Rockstar"),
        ("Tera Yaar Hoon Main", "Arijit Singh", 2018, "Friendship", "Amaal Mallik", "Sonu Ke Titu Ki Sweety"),
        ("Sun Saathiya", "Priya Saraiya", 2015, "Dance", "Sachin-Jigar", "ABCD 2"),
        ("Lungi Dance", "Yo Yo Honey Singh", 2013, "Party", "Yo Yo Honey Singh", "Chennai Express"),
        ("Badri Ki Dulhania", "Neha Kakkar", 2017, "Party", "Tanishk Bagchi", "Badrinath Ki Dulhania"),
        ("Kal Ho Naa Ho", "Sonu Nigam", 2003, "Romance", "Shankar-Ehsaan-Loy", "Kal Ho Naa Ho"),
        ("Bolna", "Arijit Singh", 2016, "Romance", "Tanishk Bagchi", "Kapoor & Sons"),
        ("Samjhawan", "Arijit Singh", 2014, "Romance", "Sharib-Toshi", "Humpty Sharma Ki Dulhania"),
        ("Nazm Nazm", "Arko", 2017, "Romance", "Arko", "Bareilly Ki Barfi"),
        ("Saiyaara", "Mohit Chauhan", 2012, "Romance", "Vishal-Shekhar", "Ek Tha Tiger"),
        ("Badtameez Dil", "Benny Dayal", 2013, "Party", "Pritam", "Yeh Jawaani Hai Deewani"),
        ("Deewani Mastani", "Shreya Ghoshal", 2015, "Classical", "Sanjay Leela Bhansali", "Bajirao Mastani"),
        ("Ajeeb Dastan Hai Yeh", "Lata Mangeshkar", 1960, "Romance", "Shankar-Jaikishan", "Dil Apna Aur Preet Parai"),
        ("Ye Shaam Mastani", "Kishore Kumar", 1971, "Romantic Pop", "R.D. Burman", "Kati Patang")
    ]
    cur.executemany("INSERT OR IGNORE INTO songs (title, singer, year, genre, composer, album) VALUES (?,?,?,?,?,?)", songs_data)

def insert_song(vals):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO songs (title, singer, year, genre, composer, album) VALUES (?,?,?,?,?,?)", vals)
    conn.commit()
    conn.close()

def query_df(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def add_song_ui():
    st.header("Add Song")
    with st.form("add_song"):
        title = st.text_input("Title")
        singer = st.text_input("Singer")
        year = st.number_input("Year", min_value=1900, max_value=2100, value=2020, step=1)
        genre = st.text_input("Genre")
        composer = st.text_input("Composer")
        album = st.text_input("Album")
        submitted = st.form_submit_button("Add")
        if submitted:
            if not title or not singer:
                st.error("Title and Singer required")
            else:
                insert_song((title.strip(), singer.strip(), int(year), genre.strip() or None, composer.strip() or None, album.strip() or None))
                st.success("Song added")

def create_playlist_by_singer_ui():
    st.header("Create Playlist by Singer")
    singer = st.text_input("Singer name")
    if st.button("Find"):
        if not singer:
            st.error("Type a singer name")
            return
        df = query_df("SELECT title, singer, year, genre, album FROM songs WHERE singer LIKE ?", (f"%{singer}%",))
        if df.empty:
            st.info("No songs found")
            return
        st.dataframe(df)
        name = st.text_input("Playlist name to save (optional)")
        if st.button("Save playlist"):
            if not name:
                st.error("Playlist name required")
            else:
                conn = get_conn()
                cur = conn.cursor()
                items = [(name, row["title"], row["singer"], row["year"], row["genre"]) for _, row in df.iterrows()]
                cur.executemany("INSERT OR IGNORE INTO playlists (playlist_name, song_title, singer, year, genre) VALUES (?,?,?,?,?)", items)
                conn.commit()
                conn.close()
                st.success("Playlist saved")

def create_playlist_by_year_genre_ui():
    st.header("Create Playlist by Year & Genre")
    year = st.number_input("Year", min_value=1900, max_value=2100, value=2020, step=1)
    genre = st.text_input("Genre (leave blank to ignore)")
    if st.button("Find"):
        if genre.strip():
            df = query_df("SELECT title, singer, year, genre, album FROM songs WHERE year = ? AND genre LIKE ?", (int(year), f"%{genre}%"))
        else:
            df = query_df("SELECT title, singer, year, genre, album FROM songs WHERE year = ?", (int(year),))
        if df.empty:
            st.info("No songs found")
            return
        st.dataframe(df)
        name = st.text_input("Playlist name to save (optional)")
        if st.button("Save playlist by year/genre"):
            if not name:
                st.error("Playlist name required")
            else:
                conn = get_conn()
                cur = conn.cursor()
                items = [(name, row["title"], row["singer"], row["year"], row["genre"]) for _, row in df.iterrows()]
                cur.executemany("INSERT OR IGNORE INTO playlists (playlist_name, song_title, singer, year, genre) VALUES (?,?,?,?,?)", items)
                conn.commit()
                conn.close()
                st.success("Playlist saved")

def open_modify_playlist_ui():
    st.header("Open / Modify Playlist")
    df = query_df("SELECT DISTINCT playlist_name FROM playlists")
    if df.empty:
        st.info("No playlists found")
        return
    playlist = st.selectbox("Choose playlist", df["playlist_name"].tolist())
    if playlist:
        items = query_df("SELECT song_title, singer FROM playlists WHERE playlist_name = ?", (playlist,))
        st.dataframe(items)
        action = st.selectbox("Action", ["None", "Add song", "Delete song"])
        if action == "Add song":
            title = st.text_input("Song title to add")
            if st.button("Add to playlist"):
                if title:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute("INSERT OR IGNORE INTO playlists (playlist_name, song_title) VALUES (?,?)", (playlist, title))
                    conn.commit()
                    conn.close()
                    st.success("Added")
                else:
                    st.error("Type title")
        elif action == "Delete song":
            title = st.selectbox("Song to remove", items["song_title"].tolist())
            if st.button("Remove"):
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("DELETE FROM playlists WHERE playlist_name = ? AND song_title = ?", (playlist, title))
                conn.commit()
                conn.close()
                st.success("Removed")

def search_songs_ui():
    st.header("Search Songs")
    col1, col2 = st.columns(2)
    with col1:
        field = st.selectbox("Field", ["title", "singer", "year", "genre", "composer"])
    with col2:
        value = st.text_input("Search value")
    if st.button("Search"):
        if not value:
            st.error("Type search value")
            return
        if field == "year":
            try:
                int_val = int(value)
                df = query_df("SELECT title, singer, year, genre, album FROM songs WHERE year = ?", (int_val,))
            except:
                st.error("Year must be a number")
                return
        else:
            df = query_df(f"SELECT title, singer, year, genre, album FROM songs WHERE {field} LIKE ?", (f"%{value}%",))
        if df.empty:
            st.info("No results")
        else:
            st.dataframe(df)

def export_db():
    conn = get_conn()
    df_songs = pd.read_sql_query("SELECT * FROM songs", conn)
    df_playlists = pd.read_sql_query("SELECT * FROM playlists", conn)
    conn.close()
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_songs.to_excel(writer, index=False, sheet_name="Songs")
        df_playlists.to_excel(writer, index=False, sheet_name="Playlists")
    buffer.seek(0)
    st.download_button("Download DB as Excel", data=buffer, file_name="music_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def main():
    st.set_page_config(page_title="Music Manager", layout="wide")
    init_db()
    st.title("🎵 Music Manager (Web)")
    menu = st.sidebar.selectbox("Menu", ["Home", "Add Song", "Playlist by Singer", "Playlist by Year/Genre", "Open/Modify Playlist", "Search", "Export"])
    if menu == "Home":
        st.write("Welcome — use the sidebar to navigate. This app uses a local SQLite DB (songs.db).")
        if st.button("Show all songs"):
            st.dataframe(query_df("SELECT title, singer, year, genre, composer, album FROM songs"))
    elif menu == "Add Song":
        add_song_ui()
    elif menu == "Playlist by Singer":
        create_playlist_by_singer_ui()
    elif menu == "Playlist by Year/Genre":
        create_playlist_by_year_genre_ui()
    elif menu == "Open/Modify Playlist":
        open_modify_playlist_ui()
    elif menu == "Search":
        search_songs_ui()
    elif menu == "Export":
        export_db()

if __name__ == "__main__":
    main()
