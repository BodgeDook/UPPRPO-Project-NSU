from fastapi import FastAPI, Query
import uvicorn
import psycopg2
import os

DB_PARAMS = {
    "dbname": "",
    "user": "",
    "password": "",  
    "host": "localhost",
    "port": "5432"
}

def connect_to_db():
    """ Подключение к PostgreSQL """
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"Error with connection to db: {e}")
        return None, None
    
def upload_vid(file_path):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            return {"error": "DB didn't connected"}
        
        with open(file_path, 'rb') as file:
            binary_data = file.read()
        filename = file_path.split("/")[-1]

        cur.execute("INSERT INTO videos (filename, file_data) VALUES (%s, %s);", (filename, binary_data))
        
        conn.commit()
        cur.close()
        conn.close()

        return {f"File: {filename} was uploaded sucessfully!"}
    
    except Exception as e:
        print(f"Exception with saving bd: {e}")
        return {"error": str(e)}
    
def download_video(filename, output_path):
    conn, cur = connect_to_db()
    if conn is None or cur is None:
        return {"error": "DB didn't connected"}
    
    cur.execute("SELECT file_data FROM videos WHERE filename = %s;", (filename,))
    result = cur.fetchone()

    if result:
        file_data = result[0]
        os.makedirs(output_path, exist_ok=True)
        with open(os.path.join(output_path, filename), 'wb') as file:
            file.write(file_data)
        print(f"video saved as: {output_path}{filename}")
    else:
        print(f"video {filename} doesn't exist")

    cur.close()
    conn.close()

upload_vid("/sql/videos/vid2.MP4")
download_video("vid2.MP4", "/sql/downloaded_videos")