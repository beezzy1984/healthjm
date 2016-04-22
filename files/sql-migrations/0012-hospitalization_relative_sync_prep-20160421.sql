
begin;

ALTER TABLE "party_relative" ADD uuid uuid;
UPDATE "party_relative"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "party_relative"
    ALTER uuid set not null,
    ADD CONSTRAINT "party_relative_uuid_unique"
        UNIQUE(uuid);


ALTER TABLE "party_contact_mechanism" ADD uuid uuid;
UPDATE "party_contact_mechanism"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "party_contact_mechanism"
    ALTER uuid set not null,
    ADD CONSTRAINT "party_contact_mechanism_uuid_unique"
        UNIQUE(uuid);



commit;
