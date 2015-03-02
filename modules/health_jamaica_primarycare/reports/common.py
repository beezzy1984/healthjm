
from trytond.modules.health_jamaica import tryton_utils as utils

__all__ = ['STATE_RO', 'STATE_INVRO', 'make_age_grouper', 'utils',
           'mk_domain_clause']


STATE_RO={'readonly':True}
STATE_INVRO={'readonly':True, 'invisible':True}

# make_age_grouper: 
# takes a list of triples with each triple representing :
# (age_group_name, min_age, age_too_old)
# Comparisons are done as min_age<= current_age < age_too_old
# So for the age group 12 - 18 years. You would put ('12-18', 12,19)
# The logic here is that a person who's 19th birthday is tomorrow is still
# 18 years old today.
# For the case of Unknown age, where dob is unset, the age group should
# use values like ('unknown age', -1, None)
# the low age must be negative and the upper limit should be None


def make_age_grouper(age_groups, ref_date, dob_field='patient.dob'):
    age_group_dict = {}
    if len(age_groups) == 2 and age_groups[0][2] == age_groups[1][1]:
        age_boundary = utils.get_dob(age_groups[0][2])
        return lambda x: (age_groups[0][0]
                          if x[dob_field] >= age_boundary 
                          else age_groups[1][0])

    # build an age lookup table using the age groups and individual ages 
    age_table = {}
    age_upper_threshold = age_lower_threshold = None
    for title, age_min, age_max in age_groups:
        if age_min is None and age_max is None:
            continue #improperly specified age group
        elif age_min is None and age_max>0:
            age_lower_threshold = age_max-1
            age_table[age_lower_threshold] = title
        elif age_min>0 and age_max is None:
            age_upper_threshold = age_min
            age_table[age_upper_threshold] = title
        elif age_min<0 and age_max is None:
            age_table[None] = title
        elif age_min>=0 and age_max>=0:
            age_table.update([(a, title) for a in range(age_min,age_max)])

    # gfailover handles the connection to the two exception clauses
    # or a default passthru for the regular age.
    # This allows us to pass in the ages higher than age_upper_threshold
    # and that what is returned is the age that represents the treshold.
    # example usage: 
    #   age_upper_threshold = 49; age_lower_threshold=13
    #   gfailover(32) == 32
    #   gfailover(52) == 49
    #   gfailover(60) == 49
    #   gfailover(10) == 13
    def gfailover(age):
        if age_upper_threshold and age >= age_upper_threshold:
            return age_upper_threshold
        elif age_lower_threshold and age <= age_lower_threshold:
            return age_lower_threshold
        return age

    # make the grouper do a simple lookup from the table
    # with a function failover that returns a result from the 3 exct sets
    get_age = utils.get_age_in_years
    def grouper(record):
        # take the age of the each record and lookup the 
        age = get_age(record[dob_field])
        # group from the age_table
        return age_table.get(age,
                             age_table.get(gfailover(age), None))
    return grouper



def mk_domain_clause(code, column='signs_and_symptoms.clinical.code'):
    '''returns a single domain clause to say column="<code>" '''
    if ' - ' in code:
        limits = code.split(' - ')
        return ['AND',
                (column, '>=', limits[0]),
                (column, '<=', limits[1])
        ]
    elif isinstance(code, (list, tuple)):
        return ['OR'] + [mk_domain_clause(k, column) for k in code]
    else:
        return (column, '=', code)