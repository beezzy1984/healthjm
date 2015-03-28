'''Utilities that make dealing with tryton idosynchrasies easier'''

import pytz
from os import path as ospath
from trytond.transaction import Transaction
from trytond.pool import Pool
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_cached_timezone = None

def negate(operator):
    '''returns the opposite operator of a domain operator. 
    e.g. if called as negate('=') it will return "!="
    '''
    converter = {u'=':u'!=', u'<':u'>', u'<=':u'>='}
    converter.update([(y,x) for x,y in converter.items()])
    return converter.get(operator, (u'not {}').format(operator))


def replace_clause_column(clause, new_column):
    '''replaces the column in a query clause. This is for clauses used
    with .search and .find methods ... domain language'''
    return (new_column, ) + tuple(clause[1:])

def negate_clause(clause):
    # ToDo: verify if this can work for all clause types
    return (clause[0], negate(clause[1]), clause[2])

def make_selection_display():
    def _get_x_display(self, field_name):
        fieldlist = getattr(self, '_fields')
        # import pdb; pdb.set_trace()
        field_selections = fieldlist[field_name].selection
        field_obj = getattr(self, field_name)
        xdict = dict(filter(lambda x: x[0], field_selections))
        return xdict.get(field_obj, '')

    return _get_x_display

def get_timezone():
    '''returns the current timezone specified for the company/facility 
    or the default which is the value in /etc/localtime'''
    global _cached_timezone
    if _cached_timezone:
        return _cached_timezone
    else:
        try:
            company = Transaction().context.get('company')
            company = Pool().get('company.company')(company)
            tz = company.get_timezone
        except:
            tz = None

    if tz:
        _cached_timezone = pytz.timezone(tz)
    elif ospath.exists('/etc/localtime'):
        _cached_timezone = pytz.tzfile.build_tzinfo('local',open('/etc/localtime', 'rb'))
    else:
        raise pytz.UnknownTimeZoneError('Cannot find suitable time zone')

    return _cached_timezone

def get_start_of_day(d, tz=None):
    '''returns a datetime object representing midnight at the start of
    the datetime passed in.'''
    dt = d if isinstance(d, date) else d.date()
    return datetime(*dt.timetuple()[:6], tzinfo=(tz if tz else d.tzinfo))

def get_start_of_next_day(d, tz=None):
    return get_start_of_day(d+timedelta(1), tz)

def get_dob(age, ref_date=None):
    '''returns the oldest date of birth for the age passed in'''
    if ref_date is None:
        ref_date = date.today()
    return ref_date - relativedelta(years=age)

def get_age_in_years(dob, ref_date=None):
    '''returns just the years portion of the full year,month,day age'''

    if dob is None:
        return None
    ref_date = ref_date or date.today()
    full_age = relativedelta(ref_date, dob)
    return full_age.years


def get_epi_week(d=None):
    '''
    Returns a tuple containing two date objects and an integer. They
    represent (sunday, saturday, weeknum) for the epidemiological week
    in which the date passed in <d> belongs.
    '''
    if d is None:
        d = date.today()

    dday = d.isoweekday()
    if dday == 7: 
        weekstart = d
    else:
        # rewind to the previous Sunday
        weekstart = d - timedelta(dday)

    weekend = weekstart + timedelta(6)

    jan1 = date(weekend.year, 1,1)
    jan1_wkday = jan1.isoweekday()%7 # modulo with 7 since we want Sunday=0

    dyear = weekend.year
    dweek = int(weekend.strftime('%U'))
    if jan1_wkday > 0: # year doesn't start on a Sunday. Life is hard
        if jan1_wkday < 4:
            dweek += 1
        elif dweek == 0 :
            dweek = 53
            dyear = weekstart.year

    return (weekstart, weekend, dyear, dweek)


def is_not_synchro():
    '''
    returns True if the effective user id of the transaction is
    greater than 0
    '''
    t = Transaction()
    print('Transaction context = [{}]'.format(repr(t.context)))
    return (t.user>0)


def get_field_states(field):
    s = field.states
    if s is None:
        return {}
    return s.copy()

def update_states(field, updates):
    '''updates a states attribute on a field with the values from <updates>.
    <updates> can be either a dictionary or list of tuples
    '''
    current_states = get_field_states(field)
    current_states.update(updates)
    return current_states
