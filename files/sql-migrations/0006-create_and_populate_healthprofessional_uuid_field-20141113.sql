
ALTER table "gnuhealth_healthprofessional" ADD uuid uuid;

UPDATE "gnuhealth_healthprofessional"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_healthprofessional"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_healthprofessional_uuid_unique" 
		UNIQUE(uuid);

