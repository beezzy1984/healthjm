

ALTER TABLE gnuhealth_hp_specialty
	ADD COLUMN is_main_specialty boolean default(false);

UPDATE gnuhealth_hp_specialty
	SET is_main_specialty = True from gnuhealth_healthprofessional a
	where gnuhealth_hp_specialty.name=a.id
	and a.main_specialty=gnuhealth_hp_specialty.id;

UPDATE gnuhealth_healthprofessional 
	set main_specialty = null;


ALTER TABLE gnuhealth_institution_specialties
	ADD COLUMN is_main_specialty boolean default(false);

UPDATE gnuhealth_institution_specialties
	SET is_main_specialty = True from gnuhealth_institution a
	where gnuhealth_institution_specialties.name=a.id
	and a.main_specialty=gnuhealth_institution_specialties.id;

UPDATE gnuhealth_institution
	SET main_specialty = null;

