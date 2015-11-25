drop table if exists users;
create table users (
    username text primary key,
    pwdhash text not null,
    realname text not null,
    privkeyenc text not null,
    pubkey text not null
);

drop table if exists friends;
create table friends (
    username text primary key,
    friendlist text
);
