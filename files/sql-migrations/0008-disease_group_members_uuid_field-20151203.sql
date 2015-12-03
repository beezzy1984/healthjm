
begin;

ALTER table "gnuhealth_disease_group_members" ADD uuid uuid;

UPDATE "gnuhealth_disease_group_members"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_disease_group_members"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_disease_group_members_uuid_unique" 
		UNIQUE(uuid);

-- -----------------------
ALTER table "gnuhealth_vaccination" ADD uuid uuid;

UPDATE "gnuhealth_vaccination"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_vaccination"
    ALTER uuid SET not null,
    ADD CONSTRAINT "gnuhealth_vaccination_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------

commit;
