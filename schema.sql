drop table if exists users;
create table users (
    username text primary key,
    pwdhash text not null,
    realname text not null,
    gender text not null,
    privkeyenc text not null,
    pubkey text not null
);

/* user is friends with user2  */
drop table if exists friends;
create table friends (
    user1 text,
    user2 text,
    PRIMARY KEY (user1, user2)
);
