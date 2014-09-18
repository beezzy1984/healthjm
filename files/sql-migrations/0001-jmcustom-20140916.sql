-- BEGIN jm_custom_001;

ALTER TABLE country_district_community
	DROP CONSTRAINT country_district_community_name_uniq;

ALTER TABLE gnuhealth_hospital_building
	DROP CONSTRAINT gnuhealth_hospital_building_institution_fkey;

ALTER TABLE gnuhealth_hospital_or
	DROP CONSTRAINT gnuhealth_hospital_or_institution_fkey;

ALTER TABLE gnuhealth_hospital_unit
	DROP CONSTRAINT gnuhealth_hospital_unit_institution_fkey;

ALTER TABLE gnuhealth_hospital_ward
	DROP CONSTRAINT gnuhealth_hospital_ward_institution_fkey;

ALTER TABLE country_post_office
	ADD COLUMN code character varying(10) NOT NULL,
	ADD COLUMN inspectorate character varying,
	ADD COLUMN subdivision integer;

COMMENT ON COLUMN country_post_office.code IS 'Code';

COMMENT ON COLUMN country_post_office.inspectorate IS 'Inspectorate';

COMMENT ON COLUMN country_post_office.subdivision IS 'Parish/Province';

ALTER TABLE gnuhealth_du
	ADD COLUMN address_street_num character varying(8);

COMMENT ON COLUMN gnuhealth_du.address_subdivision IS 'Parish/Province';

COMMENT ON COLUMN gnuhealth_du."desc" IS 'Additional Description';

COMMENT ON COLUMN gnuhealth_du.address_district_community IS 'District (JM)';

COMMENT ON COLUMN gnuhealth_du.address_post_office IS 'Post Office (JM)';

COMMENT ON COLUMN gnuhealth_du.address_street_num IS 'Street Number';

ALTER TABLE gnuhealth_institution_specialties
	ALTER COLUMN specialty SET NOT NULL;

COMMENT ON COLUMN gnuhealth_insurance.number IS 'Policy#';

COMMENT ON COLUMN gnuhealth_newborn.cephalic_perimeter IS 'Head Circumference';

COMMENT ON COLUMN gnuhealth_newborn.length IS 'Crown-Heel Length';

ALTER TABLE party_party
	ADD COLUMN firstname character varying;

UPDATE party_party 
	SET firstname = name where is_person=True;

UPDATE party_party
	set name = lastname||', '||firstname where is_person=True;


COMMENT ON COLUMN party_party."ref" IS 'UPI';

COMMENT ON COLUMN party_party.occupation IS 'Occupational Group';

COMMENT ON COLUMN party_party.father_name IS 'Father''s Name';

COMMENT ON COLUMN party_party.mother_maiden_name IS 'Mother''s Maiden Name';

COMMENT ON COLUMN party_party.firstname IS 'First name';

ALTER TABLE country_district_community
	ADD CONSTRAINT country_district_community_name_per_po_uniq UNIQUE (name, post_office);

ALTER TABLE country_post_office
	ADD CONSTRAINT country_post_office_code_uniq UNIQUE (code);

ALTER TABLE country_post_office
	ADD CONSTRAINT country_post_office_subdivision_fkey FOREIGN KEY (subdivision) REFERENCES country_subdivision(id) ON DELETE SET NULL,
	DROP CONSTRAINT country_post_office_name_uniq;

CREATE INDEX party_party_firstname_index ON party_party USING btree (firstname);

CREATE INDEX party_party_lastname_index ON party_party USING btree (lastname);

-- commit jm_custom_001;