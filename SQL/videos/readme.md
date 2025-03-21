to upload video to db:
    upload_vid("path_to_file_which_we_want_to_upload_to_db")
to download video to local machine from db:
    download_vid("filenale_which_we_want_to_download_from_db", "path_on_out_local_machine_where_we_want_to_download_file")

TABLE STRUCTURE:
  Column   | Type  | Collation | Nullable | Default 
-----------+-------+-----------+----------+---------
 filename  | text  |           | not null | 
 file_data | bytea |           | not null | 
