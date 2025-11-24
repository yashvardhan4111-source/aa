# app.py
import streamlit as st
import mysql.connector
from mysql.connector import Error
import time

st.set_page_config(page_title="Music Manager - IDLE Terminal", layout="wide")

# -------------------------
# Config (change if needed)
# -------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "Yash",
    "passwd": "mysql@123",
    # database will be used after creation
}

# -------------------------
# Terminal helpers / state
# -------------------------
if "terminal_output" not in st.session_state:
    st.session_state.terminal_output = ""

if "waiting_handler" not in st.session_state:
    st.session_state.waiting_handler = None

if "input_value" not in st.session_state:
    st.session_state.input_value = ""

if "temp" not in st.session_state:
    st.session_state.temp = {}

if "started" not in st.session_state:
    st.session_state.started = False

def terminal_print(text=""):
    """Add a line to terminal output exactly like print()."""
    st.session_state.terminal_output += str(text) + "\n"

def request_input(prompt, handler):
    """
    Show prompt like input(prompt) and set handler to be called with the reply.
    handler: function that accepts one argument (the user's input string).
    """
    terminal_print(prompt)
    st.session_state.waiting_handler = handler

def process_user_input():
    """Called when user presses Submit. Passes input to handler."""
    val = st.session_state.input_value
    st.session_state.input_value = ""
    # echo the user's input exactly like in terminal
    terminal_print(f"> {val}")
    handler = st.session_state.waiting_handler
    st.session_state.waiting_handler = None
    if handler:
        handler(val)
    else:
        # no handler means show menu again
        main_menu()

# -------------------------
# Database helpers
# -------------------------
def get_connection(specify_db=False):
    """Return a mysql connection object. If specify_db True, will use musicmanager database."""
    cfg = DB_CONFIG.copy()
    if specify_db:
        cfg["database"] = "musicmanager"
    try:
        conn = mysql.connector.connect(**cfg)
        return conn
    except Exception as e:
        terminal_print(f"Database connection error: {e}")
        return None

# -------------------------
# Program logic converted
# into state + handlers
# -------------------------

# --- Setup / create DB and tables ---
def setup_database_start(dummy=None):
    """
    Start the setup flow. This replicates the behavior in your rr.py: checks SHOW DATABASES,
    prompts the user whether to skip creation if exists, else drops and recreates.
    """
    conn = get_connection(specify_db=False)
    if not conn:
        terminal_print("Failed to connect to MySQL server with provided credentials.")
        terminal_print("Make sure MySQL server is running and DB_CONFIG is correct.")
        st.session_state.started = True
        main_menu()
        return

    cursor = conn.cursor()
    try:
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
    except Exception as e:
        terminal_print(f"Error checking databases: {e}")
        cursor.close()
        conn.close()
        st.session_state.started = True
        main_menu()
        return

    if "musicmanager" in databases:
        terminal_print("The 'musicmanager' database already exists.")
        # ask skip or recreate
        request_input("Would you like to skip database creation and continue? (yes/no): ", setup_database_choice)
        cursor.close()
        conn.close()
        return
    else:
        # create DB and tables directly
        try:
            cursor.execute("CREATE DATABASE musicmanager")
            cursor.execute("USE musicmanager")
            terminal_print("Database 'musicmanager' created successfully!")
            # create songs table
            create_songs_table = """
            CREATE TABLE IF NOT EXISTS songs (
                title VARCHAR(255) NOT NULL,
                singer VARCHAR(255) NOT NULL,
                year INT NOT NULL,
                genre VARCHAR(100),
                composer VARCHAR(255),
                album VARCHAR(255),
                PRIMARY KEY (title, singer, year)
            );
            """
            cursor.execute(create_songs_table)
            terminal_print("Songs table created successfully.")
            create_playlists_table = """
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_name VARCHAR(255) NOT NULL,
                song_title VARCHAR(255) NOT NULL,
                singer VARCHAR(255),
                year INT,
                genre VARCHAR(100),
                PRIMARY KEY (playlist_name, song_title)
            );
            """
            cursor.execute(create_playlists_table)
            terminal_print("Playlists table created successfully.")
        except Exception as e:
            terminal_print(f"Error creating database/tables: {e}")
        finally:
            cursor.close()
            conn.close()

    # Ask to add initial songs
    request_input("Would you like to add songs to the database now? (yes/no): ", setup_add_choice)

def setup_database_choice(ans):
    ans = ans.strip().lower()
    if ans == "yes":
        terminal_print("Skipping creation and continuing to program.")
        # nothing to do; proceed
        st.session_state.started = True
        main_menu()
    else:
        # drop and recreate
        conn = get_connection(specify_db=False)
        if not conn:
            terminal_print("Cannot reconnect to MySQL to drop/create DB.")
            st.session_state.started = True
            main_menu()
            return
        cursor = conn.cursor()
        try:
            cursor.execute("DROP DATABASE IF EXISTS musicmanager")
            cursor.execute("CREATE DATABASE musicmanager")
            cursor.execute("USE musicmanager")
            terminal_print("Existing database dropped. Database 'musicmanager' created successfully!")
            # create tables
            create_songs_table = """
            CREATE TABLE IF NOT EXISTS songs (
                title VARCHAR(255) NOT NULL,
                singer VARCHAR(255) NOT NULL,
                year INT NOT NULL,
                genre VARCHAR(100),
                composer VARCHAR(255),
                album VARCHAR(255),
                PRIMARY KEY (title, singer, year)
            );
            """
            cursor.execute(create_songs_table)
            terminal_print("Songs table created successfully.")
            create_playlists_table = """
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_name VARCHAR(255) NOT NULL,
                song_title VARCHAR(255) NOT NULL,
                singer VARCHAR(255),
                year INT,
                genre VARCHAR(100),
                PRIMARY KEY (playlist_name, song_title)
            );
            """
            cursor.execute(create_playlists_table)
            terminal_print("Playlists table created successfully.")
        except Exception as e:
            terminal_print(f"Error dropping/creating DB: {e}")
        finally:
            cursor.close()
            conn.close()
        # then prompt to add songs
        request_input("Would you like to add songs to the database now? (yes/no): ", setup_add_choice)

def setup_add_choice(ans):
    ans = ans.strip().lower()
    if ans == "yes":
        request_input("Choose an option to add songs:\n1. Add one by one\n2. Add multiple songs in bulk\nEnter (1/2): ", setup_add_option)
    else:
        st.session_state.started = True
        terminal_print("Skipping song addition. Proceeding to program.")
        main_menu()

def setup_add_option(choice):
    c = choice.strip()
    if c == "1":
        # start manual add sequence
        st.session_state.temp = {}
        request_input("Enter song title: ", add_manual_title)
    elif c == "2":
        # bulk insert all songs
        conn = get_connection(specify_db=True)
        if not conn:
            terminal_print("Failed to connect to musicmanager DB for bulk insert.")
            st.session_state.started = True
            main_menu()
            return
        cursor = conn.cursor()
        insert_query = """
        INSERT IGNORE INTO songs (title, singer, year, genre, composer, album)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        songs_data = bulk_songs_list()
        try:
            cursor.executemany(insert_query, songs_data)
            conn.commit()
            terminal_print(f"{cursor.rowcount} songs inserted successfully (duplicates skipped).")
        except Exception as e:
            terminal_print(f"Bulk insert error: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
        st.session_state.started = True
        main_menu()
    else:
        terminal_print("Invalid choice. Skipping song entry.")
        st.session_state.started = True
        main_menu()

def add_manual_title(val):
    st.session_state.temp["title"] = val.strip()
    request_input("Enter singer name: ", add_manual_singer)

def add_manual_singer(val):
    st.session_state.temp["singer"] = val.strip()
    request_input("Enter release year: ", add_manual_year)

def add_manual_year(val):
    try:
        st.session_state.temp["year"] = int(val.strip())
    except:
        terminal_print("Invalid year. Please enter a number.")
        request_input("Enter release year: ", add_manual_year)
        return
    request_input("Enter genre: ", add_manual_genre)

def add_manual_genre(val):
    v = val.strip()
    st.session_state.temp["genre"] = v if v != "" else None
    request_input("Enter composer name: ", add_manual_composer)

def add_manual_composer(val):
    v = val.strip()
    st.session_state.temp["composer"] = v if v != "" else None
    request_input("Enter album name: ", add_manual_album)

def add_manual_album(val):
    v = val.strip()
    st.session_state.temp["album"] = v if v != "" else None
    # insert into DB
    conn = get_connection(specify_db=True)
    if not conn:
        terminal_print("Failed to connect to DB to insert song.")
        st.session_state.started = True
        main_menu()
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO songs (title, singer, year, genre, composer, album)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            st.session_state.temp.get("title"),
            st.session_state.temp.get("singer"),
            st.session_state.temp.get("year"),
            st.session_state.temp.get("genre"),
            st.session_state.temp.get("composer"),
            st.session_state.temp.get("album"),
        ))
        conn.commit()
        terminal_print(f"Song '{st.session_state.temp.get('title')}' added successfully.")
    except Exception as e:
        terminal_print(f"Error adding song: {e}")
    finally:
        cursor.close()
        conn.close()
    request_input("Add another song? (yes/no): ", add_manual_another)

def add_manual_another(val):
    if val.strip().lower() == "yes":
        st.session_state.temp = {}
        request_input("Enter song title: ", add_manual_title)
    else:
        st.session_state.started = True
        main_menu()

# ---------- Bulk songs list (keeps your full data) ----------
def bulk_songs_list():
    # Returns the full songs list as in your rr.py
    return [
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

# ---------- Menu & core features ----------
def show_menu_text():
    terminal_print("\n" + "="*50)
    terminal_print("     MUSIC MANAGER MENU")
    terminal_print("="*50)
    terminal_print("1. Create playlist by singer")
    terminal_print("2. Create playlist by year and genre")
    terminal_print("3. Open and modify playlist")
    terminal_print("4. Search songs")
    terminal_print("5. Exit")
    terminal_print("="*50)

def main_menu(dummy=None):
    show_menu_text()
    request_input("Enter choice (1-5): ", handle_main_choice)

def handle_main_choice(choice):
    c = choice.strip()
    if c == "1":
        # create playlist by singer
        request_input("Enter singer name: ", create_playlist_by_singer)
    elif c == "2":
        request_input("Enter release year: ", create_playlist_by_year_genre_year)
    elif c == "3":
        open_modify_playlist_start()
    elif c == "4":
        search_songs_by_attributes_start()
    elif c == "5":
        terminal_print("Thank you for using Music Manager! Goodbye! 🎶")
        # stop the app
        st.session_state.waiting_handler = None
        # do not call st.stop() — just print exit note and disable further inputs
    else:
        terminal_print("Invalid choice. Try again.")
        main_menu()

# 1. Create playlist by singer
def create_playlist_by_singer(singer_name):
    singer = singer_name.strip()
    conn = get_connection(specify_db=True)
    if not conn:
        terminal_print("Failed to connect to database.")
        main_menu()
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT title, singer, year, genre, album FROM songs WHERE singer = %s", (singer,))
        songs = cursor.fetchall()
    except Exception as e:
        terminal_print(f"Error querying songs: {e}")
        cursor.close()
        conn.close()
        main_menu()
        return

    if not songs:
        terminal_print(f"No songs found for singer: {singer}")
        cursor.close()
        conn.close()
        main_menu()
        return

    terminal_print(f"\nFound {len(songs)} song(s) by {singer}:")
    for i, song in enumerate(songs, 1):
        title, sng_singer, year, genre, album = song
        terminal_print(f"  {i}. {title} ({year}) - {genre or 'Unknown'}")

    def save_choice(ans):
        if ans.strip().lower() == "yes":
            def ask_playlist_name(name):
                plname = name.strip()
                if not plname:
                    terminal_print("Invalid name.")
                    main_menu()
                    return
                # insert into playlists
                try:
                    cursor.executemany(
                        "INSERT IGNORE INTO playlists (playlist_name, song_title, singer) VALUES (%s, %s, %s)",
                        [(plname, s[0], singer) for s in songs]
                    )
                    conn.commit()
                    terminal_print(f"Playlist '{plname}' saved!")
                except Exception as e:
                    terminal_print(f"Error saving playlist: {e}")
                finally:
                    cursor.close()
                    conn.close()
                    main_menu()
            request_input("Playlist name: ", ask_playlist_name)
        else:
            cursor.close()
            conn.close()
            main_menu()
    request_input("\nSave as playlist? (yes/no): ", save_choice)

# 2. Create playlist by year and genre (two-step)
def create_playlist_by_year_genre_year(year_str):
    try:
        year = int(year_str.strip())
    except:
        terminal_print("Invalid year.")
        main_menu()
        return
    st.session_state.temp["year_for_playlist"] = year
    request_input("Enter genre: ", create_playlist_by_year_genre_genre)

def create_playlist_by_year_genre_genre(genre_str):
    year = st.session_state.temp.get("year_for_playlist")
    genre = genre_str.strip()
    conn = get_connection(specify_db=True)
    if not conn:
        terminal_print("Failed to connect to DB.")
        main_menu()
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT title, singer, year, genre, album
            FROM songs
            WHERE year = %s AND (genre = %s OR %s IS NULL)
        """, (year, genre, genre))
        songs = cursor.fetchall()
    except Exception as e:
        terminal_print(f"Error querying songs: {e}")
        cursor.close()
        conn.close()
        main_menu()
        return

    if not songs:
        terminal_print(f"No songs found for year {year} and genre '{genre}'")
        cursor.close()
        conn.close()
        main_menu()
        return

    terminal_print(f"\nFound {len(songs)} matching song(s):")
    for i, s in enumerate(songs, 1):
        terminal_print(f"  {i}. {s[0]} by {s[1]} ({s[2]})")

    def save_choice(ans):
        if ans.strip().lower() == "yes":
            def ask_playlist_name(name):
                plname = name.strip()
                if not plname:
                    terminal_print("Invalid name.")
                    main_menu()
                    return
                try:
                    cursor.executemany(
                        "INSERT IGNORE INTO playlists (playlist_name, song_title, year, genre) VALUES (%s, %s, %s, %s)",
                        [(plname, s[0], year, genre) for s in songs]
                    )
                    conn.commit()
                    terminal_print(f"Playlist '{plname}' saved!")
                except Exception as e:
                    terminal_print(f"Error: {e}")
                finally:
                    cursor.close()
                    conn.close()
                    main_menu()
            request_input("Playlist name: ", ask_playlist_name)
        else:
            cursor.close()
            conn.close()
            main_menu()
    request_input("\nSave as playlist? (yes/no): ", save_choice)

# 3. Open and modify playlist
def open_modify_playlist_start(dummy=None):
    conn = get_connection(specify_db=True)
    if not conn:
        terminal_print("Failed to connect to DB.")
        main_menu()
        return
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT DISTINCT playlist_name FROM playlists")
        playlists = cursor.fetchall()
    except Exception as e:
        terminal_print(f"Error fetching playlists: {e}")
        cursor.close()
        conn.close()
        main_menu()
        return

    if not playlists:
        terminal_print("No playlists found.")
        cursor.close()
        conn.close()
        main_menu()
        return

    terminal_print("\nAvailable Playlists:")
    for p in playlists:
        terminal_print(f"  • {p[0]}")

    def ask_name(name):
        pname = name.strip()
        cursor_inner = conn.cursor()
        try:
            cursor_inner.execute("SELECT song_title, singer FROM playlists WHERE playlist_name = %s", (pname,))
            songs = cursor_inner.fetchall()
        except Exception as e:
            terminal_print(f"Error reading playlist: {e}")
            cursor_inner.close()
            conn.close()
            main_menu()
            return

        if not songs:
            terminal_print(f"Playlist '{pname}' is empty or doesn't exist.")
            cursor_inner.close()
            conn.close()
            main_menu()
            return

        terminal_print(f"\nSongs in '{pname}':")
        for i, (title, singer) in enumerate(songs, 1):
            terminal_print(f"  {i}. {title} {f'by {singer}' if singer else ''}")

        def ask_action(action):
            a = action.strip().lower()
            if a == "add":
                def add_title(title):
                    try:
                        cursor_inner.execute("INSERT IGNORE INTO playlists (playlist_name, song_title) VALUES (%s, %s)", (pname, title.strip()))
                        conn.commit()
                        terminal_print("Added!" if cursor_inner.rowcount else "Song already in playlist.")
                    except Exception as e:
                        terminal_print(f"Error adding to playlist: {e}")
                    finally:
                        cursor_inner.close()
                        conn.close()
                        main_menu()
                request_input("Song title to add: ", add_title)
            elif a == "delete":
                def del_title(title):
                    try:
                        cursor_inner.execute("DELETE FROM playlists WHERE playlist_name = %s AND song_title = %s", (pname, title.strip()))
                        conn.commit()
                        terminal_print("Removed!" if cursor_inner.rowcount else "Song not found.")
                    except Exception as e:
                        terminal_print(f"Error removing song: {e}")
                    finally:
                        cursor_inner.close()
                        conn.close()
                        main_menu()
                request_input("Song title to remove: ", del_title)
            else:
                terminal_print("No changes made.")
                cursor_inner.close()
                conn.close()
                main_menu()

        request_input("\nAction (add/delete/none): ", ask_action)

    request_input("\nEnter playlist name: ", ask_name)

# 4. Search songs
def search_songs_by_attributes_start(dummy=None):
    terminal_print("\nSearch by:")
    terminal_print("1. Title   2. Singer   3. Year   4. Genre   5. Composer")
    request_input("Choose (1-5): ", search_songs_choice)

def search_songs_choice(choice):
    try:
        ch = int(choice.strip())
    except:
        terminal_print("Invalid choice.")
        main_menu()
        return
    if ch not in {1,2,3,4,5}:
        terminal_print("Invalid option.")
        main_menu()
        return
    st.session_state.temp["search_col"] = {1:'title',2:'singer',3:'year',4:'genre',5:'composer'}[ch]
    request_input("Enter value: ", search_songs_value)

def search_songs_value(value):
    col = st.session_state.temp.get("search_col")
    conn = get_connection(specify_db=True)
    if not conn:
        terminal_print("DB connection failed.")
        main_menu()
        return
    cursor = conn.cursor()
    query = f"SELECT title, singer, year, genre, album FROM songs WHERE {col} LIKE %s"
    try:
        cursor.execute(query, (f"%{value.strip()}%",))
        results = cursor.fetchall()
    except Exception as e:
        terminal_print(f"Search error: {e}")
        cursor.close()
        conn.close()
        main_menu()
        return

    if not results:
        terminal_print("No results found.")
        cursor.close()
        conn.close()
        main_menu()
        return

    terminal_print(f"\n{len(results)} result(s):")
    for r in results:
        terminal_print(f"  • {r[0]} by {r[1]} ({r[2]}) - {r[3] or 'Unknown'} | {r[4] or 'Single'}")
    cursor.close()
    conn.close()
    main_menu()

# -------------------------
# Initial run
# -------------------------
if not st.session_state.started:
    st.session_state.started = True
    terminal_print("\n" + "🎵" * 20)
    terminal_print("   WELCOME TO MUSIC MANAGER! 🎵")
    terminal_print("🎵" * 20)
    terminal_print("Organize, search, and enjoy your music collection!\n")
    # start setup DB flow (will prompt user)
    setup_database_start()

# -------------------------
# Streamlit UI
# -------------------------
st.markdown("## Music Manager — Terminal Mode (IDLE-style)\nType responses exactly like you would in IDLE.")
st.text_area("Terminal", value=st.session_state.terminal_output, height=520, key="terminal_area")

# Input box and submit
col1, col2 = st.columns([4,1])
with col1:
    st.text_input("Input (type and press Submit):", key="input_value")
with col2:
    if st.button("Submit"):
        process_user_input()
