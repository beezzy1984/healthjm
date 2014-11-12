
-- Create and populate UUID fields for newly synchronising models 
-- that contain existing data

--- =============================================================
ALTER table "gnuhealth_hp" ADD uuid uuid;

UPDATE "gnuhealth_hp"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_hp"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_hp_uuid_unique" 
		UNIQUE(uuid);

--- =============================================================
ALTER table "gnuhealth_patient_evaluation" ADD uuid uuid;

UPDATE "gnuhealth_patient_evaluation"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_patient_evaluation"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_patient_evaluation_uuid_unique" 
		UNIQUE(uuid);

--- =============================================================
ALTER table "gnuhealth_signs_and_symptoms" ADD uuid uuid;

UPDATE "gnuhealth_signs_and_symptoms"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_signs_and_symptoms"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_signs_and_symptoms_uuid_uniques" 
		UNIQUE(uuid);

--- =============================================================
ALTER table "gnuhealth_directions" ADD uuid uuid;

UPDATE "gnuhealth_directions"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_directions"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_directions_uuid_uniques" 
		UNIQUE(uuid);

--- =============================================================
ALTER table "gnuhealth_secondary_condition" ADD uuid uuid;

UPDATE "gnuhealth_secondary_condition"
	SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "gnuhealth_secondary_condition"
	ALTER uuid SET not null,
	ADD CONSTRAINT "gnuhealth_secondary_condition_uuid_uniques" 
		UNIQUE(uuid);