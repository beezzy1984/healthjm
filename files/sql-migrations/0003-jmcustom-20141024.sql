

-- In preparation for synchronising the AlternativeID model, this script
-- adds a uuid column to the table and calculates a unique ID for each
-- record in the table before making the column unique and not null

-- Must run this before applying git:efa1a107ad1dd75fe48ec4815bd6ae2b3ec17b04

ALTER table "gnuhealth_person_alternative_identification" ADD uuid uuid;

UPDATE "gnuhealth_person_alternative_identification"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_person_alternative_identification"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_person_alternative_identification_uuid_unique" 
		UNIQUE(uuid);


-- After running this script, you can run trytond -u health_jamaica_sync