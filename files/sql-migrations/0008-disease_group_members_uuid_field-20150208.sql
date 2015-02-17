
ALTER table "gnuhealth_disease_group_members" ADD uuid uuid;

UPDATE "gnuhealth_disease_group_members"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_disease_group_members"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_healthprofessional_uuid_unique" 
		UNIQUE(uuid);

