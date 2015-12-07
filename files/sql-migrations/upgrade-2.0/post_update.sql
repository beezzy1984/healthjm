begin;

-- set the subdivision column of gnuhealth_operational_sector to not null
Alter table gnuhealth_operational_sector alter column  subdivision set not null;


commit;