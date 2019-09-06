CREATE TABLE client (
       id UUID PRIMARY KEY,
       name TEXT NOT NULL,
       balance BIGINT NOT NULL,
       hold BIGINT NOT NULL,
       is_open BOOLEAN DEFAULT TRUE
);
