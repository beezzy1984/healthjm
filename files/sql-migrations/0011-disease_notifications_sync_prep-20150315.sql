
begin;

ALTER TABLE "gnuhealth_disease_notification_risk_disease" ADD uuid uuid;
UPDATE "gnuhealth_disease_notification_risk_disease"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "gnuhealth_disease_notification_risk_disease"
    ALTER uuid set not null,
    ADD CONSTRAINT "gnuhealth_disease_notification_risk_disease_uuid_unique"
        UNIQUE(uuid);


ALTER TABLE "gnuhealth_disease_notification_specimen" ADD uuid uuid;
UPDATE "gnuhealth_disease_notification_specimen"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "gnuhealth_disease_notification_specimen"
    ALTER uuid set not null,
    ADD CONSTRAINT "gnuhealth_disease_notification_specimen_uuid_unique"
        UNIQUE(uuid);


ALTER TABLE "gnuhealth_disease_notification_symptom" ADD uuid uuid;
UPDATE "gnuhealth_disease_notification_symptom"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "gnuhealth_disease_notification_symptom"
    ALTER uuid set not null,
    ADD CONSTRAINT "gnuhealth_disease_notification_symptom_uuid_unique"
        UNIQUE(uuid);


ALTER TABLE "gnuhealth_disease_notification_travel" ADD uuid uuid;
UPDATE "gnuhealth_disease_notification_travel"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "gnuhealth_disease_notification_travel"
    ALTER uuid set not null,
    ADD CONSTRAINT "gnuhealth_disease_notification_travel_uuid_unique"
        UNIQUE(uuid);


ALTER TABLE "gnuhealth_disease_notification_statechange" ADD uuid uuid;
UPDATE "gnuhealth_disease_notification_statechange"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);
ALTER TABLE "gnuhealth_disease_notification_statechange"
    ALTER uuid set not null,
    ADD CONSTRAINT "gnuhealth_disease_notification_statechange_uuid_unique"
        UNIQUE(uuid);


commit;
