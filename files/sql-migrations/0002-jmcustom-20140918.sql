

ALTER TABLE gnuhealth_person_alternative_identification
    ADD issuing_institution int null;

ALTER TABLE gnuhealth_person_alternative_identification 
    ADD CONSTRAINT issuing_institution_institution_fkey FOREIGN KEY(issuing_institution) REFERENCES gnuhealth_institution(id) ON DELETE SET Null;

ALTER TABLE gnuhealth_person_alternative_identification
    DROP issuedby;

