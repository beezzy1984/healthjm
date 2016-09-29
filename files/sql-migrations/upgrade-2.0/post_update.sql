begin;

-- set the subdivision column of gnuhealth_operational_sector to not null
Alter table gnuhealth_operational_sector alter column  subdivision set not null;

insert into party_relative
    (party, relative_lastname, relative_firstname, relationship,
     active, create_date, create_uid, write_date, write_uid, is_party,
     relative_country, relative_state, synchronised_instances, uuid,
     relative_address)

select
    party, 
    right(a.name, -position(' ' in a.name)) as ln,
    left(a.name, position(' ' in a.name)) as fn,
    relationship, a.active, a.create_date, a.create_uid, a.write_date,
    a.write_uid, false, a.country, a.subdivision, repeat('0', 512)::varbit,
    uuid_in(md5(random()::text || now()::text)::cstring),
    address_street_num || ' ' || street || ' ' || dc.name || ' ' || po.name
from party_address a 
    left join country_post_office po on po.id=a.post_office
    left join country_district_community dc on dc.id=a.district_community
    left join party_party p on p.id=a.party
where
    a.name is not null and trim(' ' from a.name) != '' and p.is_patient
    and a.name like '% %' and a.name not like '%, %';

-- --

insert into party_relative
    (party, relative_lastname, relative_firstname, relationship,
     active, create_date, create_uid, write_date, write_uid, is_party,
     relative_country, relative_state, synchronised_instances, uuid,
     relative_address)

select
    party, 
    trim(trailing ',' from left(a.name, position(',' in a.name))) as ln,
    right(a.name, -position(', ' in a.name)) as fn,
    relationship, a.active, a.create_date, a.create_uid, a.write_date,
    a.write_uid, false, a.country, a.subdivision, repeat('0', 512)::varbit,
    uuid_in(md5(random()::text || now()::text)::cstring),
    address_street_num || ' ' || street || ' ' || dc.name || ' ' || po.name
from party_address a 
    left join country_post_office po on po.id=a.post_office
    left join country_district_community dc on dc.id=a.district_community
    left join party_party p on p.id=a.party
where
    a.name is not null and trim(' ' from a.name) != '' and p.is_patient
    and a.name like '%, %';

-- --

insert into party_relative
    (party, relative_lastname, relative_firstname, relationship,
     active, create_date, create_uid, write_date, write_uid, is_party,
     relative_country, relative_state, synchronised_instances, uuid,
     relative_address)

select
    party,
    a.name as ln,
    '' as fn,
    relationship, a.active, a.create_date, a.create_uid, a.write_date,
    a.write_uid, false, a.country, a.subdivision, repeat('0', 512)::varbit,
    uuid_in(md5(random()::text || now()::text)::cstring),
    address_street_num || ' ' || street || ' ' || dc.name || ' ' || po.name
from party_address a
    left join country_post_office po on po.id=a.post_office
    left join country_district_community dc on dc.id=a.district_community
    left join party_party p on p.id=a.party
where
    a.name is not null and trim(' ' from a.name) != '' and p.is_patient
    and a.name not like '% %' and trim(' ' from a.name)!='';

-- --

update party_address set active=false
where (name like '% %' or trim(' ' from name) != '' or relative_id is not null)
and party in (select id from party_party where is_patient);

