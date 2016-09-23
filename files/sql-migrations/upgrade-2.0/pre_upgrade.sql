begin;

-- remove health_jamaica_seed and health_jamaica_profile modules
--- no longer needed as they have been removed from base

delete from ir_module_module where name='health_jamaica_seed';
delete from ir_module_module where name='health_jamaica_profile';

-- clear out references to uninstalled modules. We're using pip here
delete from ir_module_module where state='uninstalled';

-- Some things have moved, since health_jamaica_seed is gone:
-- specialties and ethnicities moved from seed -> health_jamaica

update ir_model_data set module='health_jamaica'
    where model in ('gnuhealth.ethnicity', 'gnuhealth.specialty')
    and module='health_jamaica_seed';

-- Access rights and permissions relate to the type of facility
-- so we're gonna tie all of them to health_jamaica_primarycare
update ir_model_data set module='health_jamaica_primarycare'
    where model in ('res.group', 'ir.ui.menu-res.group',
                    'ir.model.field.access', 'ir.model.access')
    and module='health_jamaica_seed';

-- Occupations belong to the yet installed health_jamaica_socioeconomics
update ir_model_data set module='health_jamaica_socioeconomics'
    where model = 'gnuhealth.occupation' and module='health_jamaica_seed';

-- And finally pathologies and procedures belong to health_jamaica_icd_icpm
update ir_model_data set module='health_jamaica_icd_icpm'
    where model in ('gnuhealth.procedure', 'gnuhealth.pathology')
    and module='health_jamaica_seed';


-- Update post offices and districts because they now belong to country_jamaica
update ir_model_data set module='country_jamaica'
    where model in ('country.post_office', 'country.district_community');

-- for all the institutions, update their UPIs
update party_party
    set ref='NP-I'|| substring(code for 3)||substring(code from 5 for 2) || substring(code from 8 for 3)
    where is_institution;

-- and create links to jmmoh_institutions 
insert into ir_model_data(create_uid, module, model, create_date, db_id, fs_id, "values")
    select 0, 'jmmoh_institutions', 'party.party', create_date, id, 'party_'|| code,
    $${'name':"$$||name||$$", 'ref':'$$||ref||$$', 'code': '$$||code||$$', 'is_institution':True}$$
    from party_party 
    where is_institution;

insert into ir_model_data(create_uid, module, model, create_date, db_id, fs_id)
    select 0, 'jmmoh_institutions', 'gnuhealth.institution', g.create_date, g.id, 'institution_'||g.code
    from gnuhealth_institution g left join party_party p on g.name=p.id;

-- due to laziness we're gonna delete all the institution specialties.
-- they will be recreated on upgrade anyways
delete from gnuhealth_institution_specialties;

-- Operational Areas, these are now in XML. They're not gonna change for now
insert into ir_model_data(create_uid, module, model, create_date, db_id, fs_id, "values")
    select 0, 'jmmoh_base', 'gnuhealth.operational_area', create_date, id,
    'jmmoh_oparea_'|| rtrim(lower(replace(name, ' ','')),'ern') as fs_id,
    $${'name':"$$|| name ||$$"}$$ as "values"
    from gnuhealth_operational_area;

-- operational sectors, create links in ir_model_data for them
Insert into ir_model_data(create_uid, module, model, create_date, db_id, fs_id, "values")
    select 0, 'jmmoh_base', 'gnuhealth.operational_sector', o.create_date, o.id,
    'jmsector_' ||split_part(p.code, '-', 2) || '_'||substring(md5(replace(split_part(rtrim(o.name,' '), ' - ', 2), '  ',' ')) for 5) as fs_id,
    $${'name':"$$||o.name||$$"}$$ as "values"
    from gnuhealth_operational_sector o, country_subdivision p
    where p.name = split_part(o.name, ' - ', 1) and
    p.country = 89;

-- institution vs sector relationships, those have to go
delete from gnuhealth_institution_operationalsector;

--this table is gonna lose its uuid field so, we'll make it not required now.
Alter table gnuhealth_institution_operationalsector alter column uuid drop not null;


-- create stubs for the modules upon which we depend so we don't have to 
-- touch the code
insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_encounter', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_jamaica_pediatrics', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_jamaica_socioeconomics', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_jamaica_icd_icpm', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_pediatrics_growth_charts', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_pediatrics_growth_charts_who', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_disease_notification', 'installed');

insert into "ir_module_module"(create_date, create_uid, name, state)
    values(now(), 0, 'health_triage_queue', 'installed');


-- clear out health professional specialties with specialty=Null
delete from gnuhealth_hp_specialty where specialty is null;

-- prepare disease groups and vaccinations for synchro
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
ALTER table "party_contact_mechanism" ADD uuid uuid;

UPDATE "party_contact_mechanism"
    SET uuid = uuid_in(md5(random()::text || now()::text)::cstring);

ALTER table "party_contact_mechanism"
    ALTER uuid SET not null,
    ADD CONSTRAINT "party_contact_mechanism_uuid_unique" 
        UNIQUE(uuid);

-- -----------------------

-- patient register report has changed name in xml, update model data
update ir_model_data
    set fs_id='healthjm_report_patientregister'
    where fs_id='jmreport_patientregister' and module='health_jamaica';

update ir_model_data
    set fs_id='healthjm_report_patientregister_wdisease'
    where fs_id='jmreport_patientregister_wdisease' and module='health_jamaica';




-- done 
commit;