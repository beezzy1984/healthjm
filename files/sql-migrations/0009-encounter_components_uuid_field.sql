begin;

-- ------------------


ALTER table "gnuhealth_encounter" ADD uuid uuid;

UPDATE "gnuhealth_encounter"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_encounter"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_encounter_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------

ALTER table "gnuhealth_encounter_clinical" ADD uuid uuid;

UPDATE "gnuhealth_encounter_clinical"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_encounter_clinical"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_encounter_clinical_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------

ALTER table "gnuhealth_encounter_procedures" ADD uuid uuid;

UPDATE "gnuhealth_encounter_procedures"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_encounter_procedures"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_encounter_procedures_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------

ALTER table "gnuhealth_encounter_anthropometry" ADD uuid uuid;

UPDATE "gnuhealth_encounter_anthropometry"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_encounter_anthropometry"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_encounter_anthropometry_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------
ALTER table "gnuhealth_encounter_ambulatory" ADD uuid uuid;

UPDATE "gnuhealth_encounter_ambulatory"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_encounter_ambulatory"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_encounter_ambulatory_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------

ALTER table "gnuhealth_encounter_mental_status" ADD uuid uuid;

UPDATE "gnuhealth_encounter_mental_status"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_encounter_mental_status"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_encounter_mental_status_uuid_unique" 
        UNIQUE(uuid);

commit;
