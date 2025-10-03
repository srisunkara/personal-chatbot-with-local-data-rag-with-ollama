-- Table: personal_chat.chat_group_dtl

-- DROP TABLE IF EXISTS personal_chat.chat_group_dtl;

CREATE TABLE IF NOT EXISTS personal_chat.chat_group_dtl
(
    id integer NOT NULL,
    user_id integer NOT NULL,
    group_name text COLLATE pg_catalog."default",
    group_desc text COLLATE pg_catalog."default",
    is_active boolean DEFAULT true,
    created_ts timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chat_group_dtl_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS personal_chat.chat_group_dtl
    OWNER to postgres;
;

-- Table: personal_chat.chat_history

-- DROP TABLE IF EXISTS personal_chat.chat_history;

CREATE TABLE IF NOT EXISTS personal_chat.chat_history
(
    id bigint NOT NULL,
    user_id integer NOT NULL DEFAULT 1,
    user_inquiry text COLLATE pg_catalog."default" NOT NULL,
    assistant_response text COLLATE pg_catalog."default" NOT NULL,
    reference_id bigint,
    chat_group_id integer,
    created_ts timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT primary_key PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS personal_chat.chat_history
    OWNER to postgres;
;
