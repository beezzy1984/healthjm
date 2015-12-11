
begin;

-- We had R505 and R508 in the old version and this one converted
-- R501 and R508 as those. However, we're gonna change it to be
-- like the old version

Update ir_model_data
    set fs_id='R508', module='health_jamaica_icd_icpm'
    where fs_id='R500' and module='health_icd10';

Update ir_model_data
    set fs_id='R505', module='health_jamaica_icd_icpm'
    where fs_id='R501' and module='health_icd10';

Update ir_model_data
    set fs_id='R500', module='health_icd10'
    where fs_id='R360' and module='health_jamaica_icd_icpm';

Update ir_model_data
    set fs_id='R501', module='health_icd10'
    where fs_id='R361' and module='health_jamaica_icd_icpm';

commit;