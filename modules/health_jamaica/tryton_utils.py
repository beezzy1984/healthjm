'''Utilities that make dealing with tryton idosynchrasies easier'''

import pytz
from os import path as ospath
from trytond.transaction import Transaction
from trytond.pool import Pool
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from proteus import config as pconfig

_cached_timezone = None

TRYTON_CONF = {'pwd':'123',
               'host':'maia.local', 'port':'8015'}

def negate(operator):
    '''returns the opposite operator of a domain operator.
    e.g. if called as negate('=') it will return "!="
    '''
    converter = {u'=': u'!=', u'<': u'>', u'<=': u'>='}
    converter.update([(y, x) for x, y in converter.items()])
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
        field_selections = fieldlist[field_name].selection
        field_obj = getattr(self, field_name)
        xdict = dict(filter(lambda x: x[0], field_selections))
        outval = xdict.get(field_obj, '')
        if outval is None:
            return ''
        else:
            return outval

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
        _cached_timezone = pytz.tzfile.build_tzinfo(
            'local',
            open('/etc/localtime', 'rb'))
    else:
        raise pytz.UnknownTimeZoneError('Cannot find suitable time zone')

    return _cached_timezone


def get_start_of_day(d, tz=None):
    '''returns a datetime object representing midnight at the start of
    the datetime passed in.'''
    if getattr(d, 'tzinfo', False):
        dt = d
    elif tz:
        dt = datetime(*d.timetuple()[:6], tzinfo=tz)
    else:
        dt = datetime(*d.timetuple()[:6], tzinfo=get_timezone())

    # now dt is a timezone aware datetime object
    # return the utc naive time for midnight at the timezone of dt

    r = datetime(*dt.timetuple()[:3], hour=0, minute=0, second=0,
                 tzinfo=dt.tzinfo)
    rdt = datetime(*r.utctimetuple()[:6])
    return rdt


def get_start_of_next_day(d, tz=None):
    return get_start_of_day(d+timedelta(1), tz)


def get_day_comp(d=None, tz=None):
    '''returns a tuple of (D1, D2) representing midnight this morning
    midnight tomorrow morning with <d> as today
    '''
    if tz is None:
        tz = get_timezone()
    else:
        tz = tz
    if d is None:
        d = datetime.now(tz=tz)
    start_of_today = get_start_of_day(d, tz)
    return (start_of_today, start_of_today+timedelta(1))


def localtime(current):
    '''returns a datetime object with local timezone. naive datetime
    assumed to be in utc'''
    tz = get_timezone()
    if current.tzinfo is None:
        # assume it's utc. convert it to timezone aware
        cdt = datetime(*current.timetuple()[:6], tzinfo=pytz.UTC,
                       microsecond=current.microsecond)
    else:
        cdt = current
    return cdt.astimezone(tz)


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


# def make_age_query(dob_field, date_ref_field):
#     '''
#     Uses the age function in the database to calculate the age at 
#     the date specified.
#     :param: instance_refs - a list of tuples with (id, ref_date)
#     '''
    
#     qry = "\n".join(["SELECT a.id as id, "
#                      "regexp_replace(AGE(%s, a.dob)::varchar, "
#                      "' ([ymd])[ayonthears ]+', '\\1 ', 'g')  as showage",
#                      "from " + tbl._Table__name + " as a",
#                      "where a.id in (%s)"])
#     qry_parm = map(int, instances)

def get_epi_week(d=None):
    '''
    Returns a tuple containing 2 date objects and a 2 integers. They
    represent (sunday, saturday, year, weeknum) for the epidemiological
    week in which the date passed in <d> belongs.
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
    jan1 = date(weekend.year, 1, 1)
    jan1_wkday = jan1.isoweekday() % 7
    # modulo with 7 since we want Sunday=0

    dyear = weekend.year
    dweek = int(weekend.strftime('%U'))
    if jan1_wkday > 0:  # year doesn't start on a Sunday. Life is hard
        if jan1_wkday < 4:  # starts before thursday
            dweek += 1
        elif dweek == 0:
            last_epi_week = get_epi_week(weekstart - timedelta(3))
            dweek = last_epi_week[-1] + 1
            dyear = weekstart.year

    return (weekstart, weekend, dyear, dweek)


def epiweek_str(d=None):
    '''reliable display of epi-week as a string
    '''
    fmt = '%d/%02d'
    if isinstance(d, (list, tuple)) and len(d) == 4:
        return fmt % d[2:]
    else:
        return fmt % get_epi_week(d)[2:]


def is_not_synchro():
    '''
    returns True if the effective user id of the transaction is
    greater than 0
    '''
    t = Transaction()
    return (t.user > 1)


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

def get_model_field_perm(model_name, field_name, perm='write',
                         default_deny=True):
    '''Returns True if the current user has the :param perm: permission
    on :param field_name: in :param model_name: model'''
    # !! Must be run within a transaction or it nah go work
    d = 0 if default_deny else 1
    FieldAccess = Pool().get('ir.model.field.access')
    user_access = FieldAccess.get_access([model_name])[model_name]
    permdict = user_access.get(field_name, {perm: d})
    user_has_perm = bool(permdict[perm])
    return user_has_perm

def get_elapsed_time(timefrom, to_time):
    '''This function accepts a datetime.datetime object 
       and calculates the amount of time elapsed and 
       returns a string  in the format years months day 
       hours seconds example 1d 2h 10m 5s'''

    if not isinstance(timefrom, datetime) or \
    not isinstance(to_time, datetime):
        return ""

    timeamount = to_time - timefrom
    #months = (timeamount.days / 7) / 4
    #weeks = (timeamount.days / 7) % 4
    #days = timeamount.days % 7
    hours = ((timeamount.seconds / 60) / 60) % 24
    minutes = (timeamount.seconds / 60) % 60
    #seconds = timeamount.seconds % 60
    def build_time_str(int_time=0, type_name=""):
        '''This function takes a an int called int_time
           and a string called type_name
           which is the amount of integer time for 
           the time quantifier called type_name'''
        time_quantifiers = {'month':'M', 'week':'w', 'day': 'd', 'hour': ':', 
                            'minute': ':', 'second': ':'}
        if not isinstance(int_time, int) or type_name not in time_quantifiers\
        or not isinstance(type_name, str):
            return '00:'
        if type_name == 'day' and int_time > 0:
            return '%d%s ' % (int_time, time_quantifiers[type_name])
        elif type_name == 'day' and int_time < 1:
            return ''

        return '%02d%s' % (int_time, time_quantifiers[type_name])

    return build_time_str(timeamount.days, 'day') + build_time_str(hours, 'hour') + \
    build_time_str(minutes, 'minute')[:-1]
    # + build_time_str(seconds, 'second')[:-1]

def test_database_config(config_file=None, institution_name=None, database_name=None):
    """Defines database configuration for module testing"""
    if config_file is None:
        config_file = ''.join(
            ['/home/randy/Projects/MOH/Cloned/healthjm',
             '/modules/health_jamaica/files/test_trytond.conf'])

    if institution_name is None:
        institution_name = 'May Pen'

    if database_name is None:
        print 'Database name is needed'
        return

    if TRYTON_CONF is not None:
        tryton_conf = TRYTON_CONF
        tryton_conf['conffile'], tryton_conf['institution'] = config_file, institution_name
        tryton_conf['dbname'] = database_name
    else:
        tryton_conf = {'pwd':'123',
                       'conffile': config_file,
                       'dbname':database_name, 'host':'maia.local', 'port':'8015',
                       'institution': institution_name}

    def get_pconfig():
        """Returns a tryton configuration settings"""
        return pconfig.set_trytond(tryton_conf['dbname'],
                                   user='admin',
                                   #database_type=test_database_type.lower(),
                                   config_file=tryton_conf['conffile'])

    return get_pconfig()
