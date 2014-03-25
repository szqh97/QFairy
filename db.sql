CREATE TABLE qvod_task(
       "id" integer primary key autoincrement,
       "qvod_url" text not null,
       "hash_code" varchar(256) not null unique,
       "created_at" timestamp not null default "0000-00-00 00:00:00", 
       "updated_at" timestamp not null default current_timestamp,
       "download_url" varchar(512), 
       "filename" text,
       "status" varchar(100) default "initialized",
       "downloader_pid" interger default -1
);
