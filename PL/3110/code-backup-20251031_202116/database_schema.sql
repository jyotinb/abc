--
-- PostgreSQL database dump
--

-- Dumped from database version 14.17 (Ubuntu 14.17-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.17 (Ubuntu 14.17-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: cleanup_old_partitions(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.cleanup_old_partitions() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    partition_record RECORD;
    partition_date DATE;
    cutoff_date DATE;
BEGIN
    cutoff_date := CURRENT_DATE - INTERVAL '1 year';
    
    -- Drop old mqtt_messages partitions
    FOR partition_record IN 
        SELECT tablename FROM pg_tables 
        WHERE tablename LIKE 'mqtt_messages_20%' AND schemaname = 'public'
    LOOP
        partition_date := TO_DATE(SUBSTRING(partition_record.tablename FROM 15), 'YYYY_MM');
        IF partition_date < cutoff_date THEN
            EXECUTE 'DROP TABLE IF EXISTS ' || partition_record.tablename;
            RAISE NOTICE 'Dropped: %', partition_record.tablename;
        END IF;
    END LOOP;
    
    -- Drop old sensor_readings partitions
    FOR partition_record IN 
        SELECT tablename FROM pg_tables 
        WHERE tablename LIKE 'sensor_readings_20%' AND schemaname = 'public'
    LOOP
        partition_date := TO_DATE(SUBSTRING(partition_record.tablename FROM 17), 'YYYY_MM');
        IF partition_date < cutoff_date THEN
            EXECUTE 'DROP TABLE IF EXISTS ' || partition_record.tablename;
            RAISE NOTICE 'Dropped: %', partition_record.tablename;
        END IF;
    END LOOP;
END;
$$;


--
-- Name: create_next_month_partitions(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.create_next_month_partitions() RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
    next_month_start DATE;
    next_month_end DATE;
    partition_suffix TEXT;
BEGIN
    next_month_start := DATE_TRUNC('month', CURRENT_DATE + INTERVAL '2 months');
    next_month_end := next_month_start + INTERVAL '1 month';
    partition_suffix := TO_CHAR(next_month_start, 'YYYY_MM');
    
    -- Create mqtt_messages partition
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS mqtt_messages_%s PARTITION OF mqtt_messages 
         FOR VALUES FROM (%L) TO (%L)',
        partition_suffix, next_month_start, next_month_end
    );
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_mqtt_%s_zone_ts ON mqtt_messages_%s (zone_id, timestamp DESC)',
        partition_suffix, partition_suffix
    );
    
    -- Create sensor_readings partition
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS sensor_readings_%s PARTITION OF sensor_readings 
         FOR VALUES FROM (%L) TO (%L)',
        partition_suffix, next_month_start, next_month_end
    );
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_sensor_%s_zone_var_ts ON sensor_readings_%s (zone_id, variable_name, timestamp DESC)',
        partition_suffix, partition_suffix
    );
    
    -- Create hourly partition
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS sensor_readings_hourly_%s PARTITION OF sensor_readings_hourly 
         FOR VALUES FROM (%L) TO (%L)',
        partition_suffix, next_month_start, next_month_end
    );
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_hourly_%s_zone_var ON sensor_readings_hourly_%s (zone_id, variable_name, hour DESC)',
        partition_suffix, partition_suffix
    );
    
    RAISE NOTICE 'Created partitions for %', TO_CHAR(next_month_start, 'YYYY-MM');
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id uuid NOT NULL,
    name character varying NOT NULL,
    email character varying,
    phone character varying,
    address character varying,
    is_active boolean,
    subscription_tier character varying,
    max_devices integer,
    settings json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: devices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.devices (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    device_number character varying NOT NULL,
    name character varying NOT NULL,
    description character varying,
    topic_name character varying NOT NULL,
    mqtt_username character varying,
    mqtt_password character varying,
    is_active boolean,
    is_online boolean,
    last_seen timestamp without time zone,
    config json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    zone_id uuid
);


--
-- Name: mqtt_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mqtt_messages (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    topic character varying(500) NOT NULL,
    direction character varying(20),
    payload jsonb NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    received_at timestamp without time zone DEFAULT now(),
    zone_topic_id uuid,
    CONSTRAINT mqtt_messages_direction_check CHECK (((direction)::text = ANY ((ARRAY['in'::character varying, 'out'::character varying])::text[])))
)
PARTITION BY RANGE ("timestamp");


--
-- Name: mqtt_messages_2025_11; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mqtt_messages_2025_11 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    topic character varying(500) NOT NULL,
    direction character varying(20),
    payload jsonb NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    received_at timestamp without time zone DEFAULT now(),
    zone_topic_id uuid,
    CONSTRAINT mqtt_messages_direction_check CHECK (((direction)::text = ANY ((ARRAY['in'::character varying, 'out'::character varying])::text[])))
);


--
-- Name: mqtt_messages_2025_12; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mqtt_messages_2025_12 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    topic character varying(500) NOT NULL,
    direction character varying(20),
    payload jsonb NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    received_at timestamp without time zone DEFAULT now(),
    zone_topic_id uuid,
    CONSTRAINT mqtt_messages_direction_check CHECK (((direction)::text = ANY ((ARRAY['in'::character varying, 'out'::character varying])::text[])))
);


--
-- Name: mqtt_messages_2026_01; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.mqtt_messages_2026_01 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    topic character varying(500) NOT NULL,
    direction character varying(20),
    payload jsonb NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    received_at timestamp without time zone DEFAULT now(),
    zone_topic_id uuid,
    CONSTRAINT mqtt_messages_direction_check CHECK (((direction)::text = ANY ((ARRAY['in'::character varying, 'out'::character varying])::text[])))
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid NOT NULL,
    name character varying NOT NULL,
    description character varying,
    permissions json,
    created_at timestamp without time zone
);


--
-- Name: sensor_readings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    value_numeric numeric(12,4),
    value_boolean boolean,
    value_text text,
    unit character varying(50),
    created_at timestamp without time zone DEFAULT now()
)
PARTITION BY RANGE ("timestamp");


--
-- Name: sensor_readings_2025_11; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_2025_11 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    value_numeric numeric(12,4),
    value_boolean boolean,
    value_text text,
    unit character varying(50),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sensor_readings_2025_12; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_2025_12 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    value_numeric numeric(12,4),
    value_boolean boolean,
    value_text text,
    unit character varying(50),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sensor_readings_2026_01; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_2026_01 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    value_numeric numeric(12,4),
    value_boolean boolean,
    value_text text,
    unit character varying(50),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sensor_readings_daily; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_daily (
    id uuid DEFAULT gen_random_uuid(),
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    date date NOT NULL,
    variable_name character varying(100) NOT NULL,
    avg_value numeric(12,4),
    min_value numeric(12,4),
    max_value numeric(12,4),
    count integer,
    sum_value numeric(12,4),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sensor_readings_hourly; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_hourly (
    id uuid DEFAULT gen_random_uuid(),
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    hour timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    avg_value numeric(12,4),
    min_value numeric(12,4),
    max_value numeric(12,4),
    count integer,
    sum_value numeric(12,4),
    created_at timestamp without time zone DEFAULT now()
)
PARTITION BY RANGE (hour);


--
-- Name: sensor_readings_hourly_2025_11; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_hourly_2025_11 (
    id uuid DEFAULT gen_random_uuid(),
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    hour timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    avg_value numeric(12,4),
    min_value numeric(12,4),
    max_value numeric(12,4),
    count integer,
    sum_value numeric(12,4),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sensor_readings_hourly_2025_12; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_hourly_2025_12 (
    id uuid DEFAULT gen_random_uuid(),
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    hour timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    avg_value numeric(12,4),
    min_value numeric(12,4),
    max_value numeric(12,4),
    count integer,
    sum_value numeric(12,4),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sensor_readings_hourly_2026_01; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sensor_readings_hourly_2026_01 (
    id uuid DEFAULT gen_random_uuid(),
    zone_id uuid NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    hour timestamp without time zone NOT NULL,
    variable_name character varying(100) NOT NULL,
    avg_value numeric(12,4),
    min_value numeric(12,4),
    max_value numeric(12,4),
    count integer,
    sum_value numeric(12,4),
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: telemetry; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.telemetry (
    "time" timestamp without time zone NOT NULL,
    device_id uuid NOT NULL,
    company_id uuid NOT NULL,
    zone_id uuid,
    temperature double precision,
    humidity double precision,
    light_level double precision,
    x_relays integer,
    y_relays integer,
    raw_data json
);


--
-- Name: user_devices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_devices (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    device_id uuid NOT NULL,
    access_level character varying(20) DEFAULT 'read'::character varying,
    assigned_at timestamp without time zone DEFAULT now(),
    assigned_by uuid
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    name character varying NOT NULL,
    is_active boolean,
    is_superuser boolean,
    company_id uuid,
    role_id uuid,
    permissions json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    role character varying(50) DEFAULT 'user'::character varying
);


--
-- Name: zone_topics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zone_topics (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    topic_path character varying(500) NOT NULL,
    direction character varying(20),
    description text,
    qos integer DEFAULT 1,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    CONSTRAINT zone_topics_direction_check CHECK (((direction)::text = ANY ((ARRAY['publish'::character varying, 'subscribe'::character varying, 'both'::character varying])::text[]))),
    CONSTRAINT zone_topics_qos_check CHECK ((qos = ANY (ARRAY[0, 1, 2])))
);


--
-- Name: TABLE zone_topics; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.zone_topics IS 'Multiple MQTT topics can be defined per zone (sensors, commands, status, etc.)';


--
-- Name: COLUMN zone_topics.direction; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.zone_topics.direction IS 'publish = device sends data, subscribe = device receives commands, both = bidirectional';


--
-- Name: zone_variables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zone_variables (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    zone_id uuid NOT NULL,
    variable_name character varying(100) NOT NULL,
    display_name character varying(200),
    json_path character varying(500),
    bit_position integer,
    parent_key character varying(100),
    data_type character varying(50) NOT NULL,
    unit character varying(50),
    transform_formula character varying(500),
    min_value numeric,
    max_value numeric,
    display_order integer DEFAULT 0,
    chart_color character varying(20),
    icon character varying(50),
    is_visible boolean DEFAULT true,
    category character varying(50),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    zone_topic_id uuid,
    CONSTRAINT zone_variables_bit_position_check CHECK (((bit_position >= 0) AND (bit_position <= 7))),
    CONSTRAINT zone_variables_data_type_check CHECK (((data_type)::text = ANY ((ARRAY['number'::character varying, 'boolean'::character varying, 'string'::character varying, 'json'::character varying])::text[])))
);


--
-- Name: zones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.zones (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    device_id uuid NOT NULL,
    name character varying NOT NULL,
    topic_name character varying NOT NULL,
    description character varying,
    optimal_temp_min double precision,
    optimal_temp_max double precision,
    optimal_humidity_min double precision,
    optimal_humidity_max double precision,
    relay_config json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    mqtt_publish_topic character varying(500),
    mqtt_subscribe_topic character varying(500),
    mqtt_qos integer DEFAULT 1,
    is_mqtt_active boolean DEFAULT true,
    mqtt_topic character varying(500)
);


--
-- Name: COLUMN zones.topic_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.zones.topic_name IS 'Legacy topic field - kept for compatibility';


--
-- Name: COLUMN zones.mqtt_publish_topic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.zones.mqtt_publish_topic IS 'Topic where device publishes data (sensor readings)';


--
-- Name: COLUMN zones.mqtt_subscribe_topic; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.zones.mqtt_subscribe_topic IS 'Topic where device subscribes for commands';


--
-- Name: mqtt_messages_2025_11; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages ATTACH PARTITION public.mqtt_messages_2025_11 FOR VALUES FROM ('2025-11-01 00:00:00') TO ('2025-12-01 00:00:00');


--
-- Name: mqtt_messages_2025_12; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages ATTACH PARTITION public.mqtt_messages_2025_12 FOR VALUES FROM ('2025-12-01 00:00:00') TO ('2026-01-01 00:00:00');


--
-- Name: mqtt_messages_2026_01; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages ATTACH PARTITION public.mqtt_messages_2026_01 FOR VALUES FROM ('2026-01-01 00:00:00') TO ('2026-02-01 00:00:00');


--
-- Name: sensor_readings_2025_11; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings ATTACH PARTITION public.sensor_readings_2025_11 FOR VALUES FROM ('2025-11-01 00:00:00') TO ('2025-12-01 00:00:00');


--
-- Name: sensor_readings_2025_12; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings ATTACH PARTITION public.sensor_readings_2025_12 FOR VALUES FROM ('2025-12-01 00:00:00') TO ('2026-01-01 00:00:00');


--
-- Name: sensor_readings_2026_01; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings ATTACH PARTITION public.sensor_readings_2026_01 FOR VALUES FROM ('2026-01-01 00:00:00') TO ('2026-02-01 00:00:00');


--
-- Name: sensor_readings_hourly_2025_11; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly ATTACH PARTITION public.sensor_readings_hourly_2025_11 FOR VALUES FROM ('2025-11-01 00:00:00') TO ('2025-12-01 00:00:00');


--
-- Name: sensor_readings_hourly_2025_12; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly ATTACH PARTITION public.sensor_readings_hourly_2025_12 FOR VALUES FROM ('2025-12-01 00:00:00') TO ('2026-01-01 00:00:00');


--
-- Name: sensor_readings_hourly_2026_01; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly ATTACH PARTITION public.sensor_readings_hourly_2026_01 FOR VALUES FROM ('2026-01-01 00:00:00') TO ('2026-02-01 00:00:00');


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (id);


--
-- Name: mqtt_messages mqtt_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages
    ADD CONSTRAINT mqtt_messages_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: mqtt_messages_2025_11 mqtt_messages_2025_11_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages_2025_11
    ADD CONSTRAINT mqtt_messages_2025_11_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: mqtt_messages_2025_12 mqtt_messages_2025_12_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages_2025_12
    ADD CONSTRAINT mqtt_messages_2025_12_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: mqtt_messages_2026_01 mqtt_messages_2026_01_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.mqtt_messages_2026_01
    ADD CONSTRAINT mqtt_messages_2026_01_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: sensor_readings sensor_readings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings
    ADD CONSTRAINT sensor_readings_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: sensor_readings_2025_11 sensor_readings_2025_11_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_2025_11
    ADD CONSTRAINT sensor_readings_2025_11_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: sensor_readings_2025_12 sensor_readings_2025_12_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_2025_12
    ADD CONSTRAINT sensor_readings_2025_12_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: sensor_readings_2026_01 sensor_readings_2026_01_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_2026_01
    ADD CONSTRAINT sensor_readings_2026_01_pkey PRIMARY KEY (id, "timestamp");


--
-- Name: sensor_readings_daily sensor_readings_daily_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_daily
    ADD CONSTRAINT sensor_readings_daily_pkey PRIMARY KEY (zone_id, date, variable_name);


--
-- Name: sensor_readings_hourly sensor_readings_hourly_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly
    ADD CONSTRAINT sensor_readings_hourly_pkey PRIMARY KEY (zone_id, hour, variable_name);


--
-- Name: sensor_readings_hourly_2025_11 sensor_readings_hourly_2025_11_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly_2025_11
    ADD CONSTRAINT sensor_readings_hourly_2025_11_pkey PRIMARY KEY (zone_id, hour, variable_name);


--
-- Name: sensor_readings_hourly_2025_12 sensor_readings_hourly_2025_12_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly_2025_12
    ADD CONSTRAINT sensor_readings_hourly_2025_12_pkey PRIMARY KEY (zone_id, hour, variable_name);


--
-- Name: sensor_readings_hourly_2026_01 sensor_readings_hourly_2026_01_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_hourly_2026_01
    ADD CONSTRAINT sensor_readings_hourly_2026_01_pkey PRIMARY KEY (zone_id, hour, variable_name);


--
-- Name: telemetry telemetry_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_pkey PRIMARY KEY ("time", device_id);


--
-- Name: devices uix_company_device; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT uix_company_device UNIQUE (company_id, device_number);


--
-- Name: user_devices user_devices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_pkey PRIMARY KEY (id);


--
-- Name: user_devices user_devices_user_id_device_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_user_id_device_id_key UNIQUE (user_id, device_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: zone_topics zone_topics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_topics
    ADD CONSTRAINT zone_topics_pkey PRIMARY KEY (id);


--
-- Name: zone_topics zone_topics_zone_id_topic_path_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_topics
    ADD CONSTRAINT zone_topics_zone_id_topic_path_key UNIQUE (zone_id, topic_path);


--
-- Name: zone_variables zone_variables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_variables
    ADD CONSTRAINT zone_variables_pkey PRIMARY KEY (id);


--
-- Name: zone_variables zone_variables_zone_id_variable_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_variables
    ADD CONSTRAINT zone_variables_zone_id_variable_name_key UNIQUE (zone_id, variable_name);


--
-- Name: zones zones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zones
    ADD CONSTRAINT zones_pkey PRIMARY KEY (id);


--
-- Name: idx_daily_zone_var; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_daily_zone_var ON public.sensor_readings_daily USING btree (zone_id, variable_name, date DESC);


--
-- Name: idx_hourly_2025_11_zone_var; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hourly_2025_11_zone_var ON public.sensor_readings_hourly_2025_11 USING btree (zone_id, variable_name, hour DESC);


--
-- Name: idx_mqtt_2025_11_zone_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mqtt_2025_11_zone_ts ON public.mqtt_messages_2025_11 USING btree (zone_id, "timestamp" DESC);


--
-- Name: idx_mqtt_2025_12_zone_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mqtt_2025_12_zone_ts ON public.mqtt_messages_2025_12 USING btree (zone_id, "timestamp" DESC);


--
-- Name: idx_mqtt_2026_01_zone_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mqtt_2026_01_zone_ts ON public.mqtt_messages_2026_01 USING btree (zone_id, "timestamp" DESC);


--
-- Name: idx_mqtt_messages_2025_11_zone_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mqtt_messages_2025_11_zone_topic ON public.mqtt_messages_2025_11 USING btree (zone_topic_id);


--
-- Name: idx_mqtt_messages_2025_12_zone_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mqtt_messages_2025_12_zone_topic ON public.mqtt_messages_2025_12 USING btree (zone_topic_id);


--
-- Name: idx_mqtt_messages_2026_01_zone_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mqtt_messages_2026_01_zone_topic ON public.mqtt_messages_2026_01 USING btree (zone_topic_id);


--
-- Name: idx_sensor_2025_11_zone_var_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sensor_2025_11_zone_var_ts ON public.sensor_readings_2025_11 USING btree (zone_id, variable_name, "timestamp" DESC);


--
-- Name: idx_sensor_2025_12_zone_var_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sensor_2025_12_zone_var_ts ON public.sensor_readings_2025_12 USING btree (zone_id, variable_name, "timestamp" DESC);


--
-- Name: idx_sensor_2026_01_zone_var_ts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sensor_2026_01_zone_var_ts ON public.sensor_readings_2026_01 USING btree (zone_id, variable_name, "timestamp" DESC);


--
-- Name: idx_telemetry_company_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_telemetry_company_time ON public.telemetry USING btree (company_id, "time");


--
-- Name: idx_telemetry_time_device; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_telemetry_time_device ON public.telemetry USING btree ("time", device_id);


--
-- Name: idx_user_devices_device; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_devices_device ON public.user_devices USING btree (device_id);


--
-- Name: idx_user_devices_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_devices_user ON public.user_devices USING btree (user_id);


--
-- Name: idx_zone_topics_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_topics_active ON public.zone_topics USING btree (zone_id, is_active);


--
-- Name: idx_zone_topics_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_topics_zone ON public.zone_topics USING btree (zone_id);


--
-- Name: idx_zone_variables_topic; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_variables_topic ON public.zone_variables USING btree (zone_topic_id);


--
-- Name: idx_zone_variables_zone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_zone_variables_zone ON public.zone_variables USING btree (zone_id, display_order);


--
-- Name: ix_companies_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_companies_name ON public.companies USING btree (name);


--
-- Name: ix_devices_device_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_devices_device_number ON public.devices USING btree (device_number);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: mqtt_messages_2025_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.mqtt_messages_pkey ATTACH PARTITION public.mqtt_messages_2025_11_pkey;


--
-- Name: mqtt_messages_2025_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.mqtt_messages_pkey ATTACH PARTITION public.mqtt_messages_2025_12_pkey;


--
-- Name: mqtt_messages_2026_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.mqtt_messages_pkey ATTACH PARTITION public.mqtt_messages_2026_01_pkey;


--
-- Name: sensor_readings_2025_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.sensor_readings_pkey ATTACH PARTITION public.sensor_readings_2025_11_pkey;


--
-- Name: sensor_readings_2025_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.sensor_readings_pkey ATTACH PARTITION public.sensor_readings_2025_12_pkey;


--
-- Name: sensor_readings_2026_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.sensor_readings_pkey ATTACH PARTITION public.sensor_readings_2026_01_pkey;


--
-- Name: sensor_readings_hourly_2025_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.sensor_readings_hourly_pkey ATTACH PARTITION public.sensor_readings_hourly_2025_11_pkey;


--
-- Name: sensor_readings_hourly_2025_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.sensor_readings_hourly_pkey ATTACH PARTITION public.sensor_readings_hourly_2025_12_pkey;


--
-- Name: sensor_readings_hourly_2026_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.sensor_readings_hourly_pkey ATTACH PARTITION public.sensor_readings_hourly_2026_01_pkey;


--
-- Name: devices devices_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: devices devices_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id);


--
-- Name: mqtt_messages mqtt_messages_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.mqtt_messages
    ADD CONSTRAINT mqtt_messages_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: mqtt_messages mqtt_messages_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.mqtt_messages
    ADD CONSTRAINT mqtt_messages_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: mqtt_messages mqtt_messages_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.mqtt_messages
    ADD CONSTRAINT mqtt_messages_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id) ON DELETE CASCADE;


--
-- Name: mqtt_messages mqtt_messages_zone_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.mqtt_messages
    ADD CONSTRAINT mqtt_messages_zone_topic_id_fkey FOREIGN KEY (zone_topic_id) REFERENCES public.zone_topics(id) ON DELETE SET NULL;


--
-- Name: sensor_readings sensor_readings_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.sensor_readings
    ADD CONSTRAINT sensor_readings_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: sensor_readings_daily sensor_readings_daily_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_daily
    ADD CONSTRAINT sensor_readings_daily_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: sensor_readings_daily sensor_readings_daily_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_daily
    ADD CONSTRAINT sensor_readings_daily_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: sensor_readings_daily sensor_readings_daily_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sensor_readings_daily
    ADD CONSTRAINT sensor_readings_daily_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id) ON DELETE CASCADE;


--
-- Name: sensor_readings sensor_readings_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.sensor_readings
    ADD CONSTRAINT sensor_readings_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: sensor_readings_hourly sensor_readings_hourly_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.sensor_readings_hourly
    ADD CONSTRAINT sensor_readings_hourly_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: sensor_readings_hourly sensor_readings_hourly_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.sensor_readings_hourly
    ADD CONSTRAINT sensor_readings_hourly_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: sensor_readings_hourly sensor_readings_hourly_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.sensor_readings_hourly
    ADD CONSTRAINT sensor_readings_hourly_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id) ON DELETE CASCADE;


--
-- Name: sensor_readings sensor_readings_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.sensor_readings
    ADD CONSTRAINT sensor_readings_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id) ON DELETE CASCADE;


--
-- Name: telemetry telemetry_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: telemetry telemetry_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- Name: telemetry telemetry_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.telemetry
    ADD CONSTRAINT telemetry_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id);


--
-- Name: user_devices user_devices_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: user_devices user_devices_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id) ON DELETE CASCADE;


--
-- Name: user_devices user_devices_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_devices
    ADD CONSTRAINT user_devices_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: zone_topics zone_topics_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_topics
    ADD CONSTRAINT zone_topics_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id) ON DELETE CASCADE;


--
-- Name: zone_variables zone_variables_zone_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_variables
    ADD CONSTRAINT zone_variables_zone_id_fkey FOREIGN KEY (zone_id) REFERENCES public.zones(id) ON DELETE CASCADE;


--
-- Name: zone_variables zone_variables_zone_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zone_variables
    ADD CONSTRAINT zone_variables_zone_topic_id_fkey FOREIGN KEY (zone_topic_id) REFERENCES public.zone_topics(id) ON DELETE CASCADE;


--
-- Name: zones zones_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zones
    ADD CONSTRAINT zones_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: zones zones_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.zones
    ADD CONSTRAINT zones_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(id);


--
-- PostgreSQL database dump complete
--

