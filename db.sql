drop table if exists qvod_tasks;
create table qvod_tasks
(
    id              int(10) unsigned  not null AUTO_INCREMENT,
    qvod_url        varchar(1024) not null,
    hash_code       varchar(128) not null,
    created_at      timestamp not null default '0000-00-00 00:00:00',
    updated_at      timestamp not null default '0000-00-00 00:00:00',
    download_url    varchar(1024),
    filename        varchar(1024),
    status          enum('initialized', 'error', 'processing', 'succeed') not null default 'initialized',
    primary key (id),
    unique key hash_id(hash_code)
)
ENGINE=InnoDB DEFAULT CHARSET=utf8;
