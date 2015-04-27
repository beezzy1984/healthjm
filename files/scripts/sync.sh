#! /bin/bash
#
#   sync.sh  - Copyright 2014 - 2015, Ministry of Health (Jamaica) 
#   written by Marc Murray <murraym@moh.gov.jm>
#   Handles interactions the celery daemon and setting up of synchro-engine
#

# handles the initial startup and cli options
debugging=false
celeryfg=false
celerycallact=""
celeryact="start"
conffile="~/.tryton/syncrc"

log() {
  test $debugging && echo "$1"
  # test -x "$LOGGER" && $LOGGER -p $LOGLEVEL "$1"
}

SYNC_CONFIG='syncconf'

SYNC_WAIT=300

MYDIR="$(dirname $0)"
PURGE_AT_STARTUP=false
#----------------------------------------------------------------------
minit(){
    source "$conffile"
    source "$VIRTUAL_ENV/bin/activate"
     WORKDIR="$(pwd)"
    # calculate the directory path by changing into the folder and using pwd
    cd $MYDIR

    MYDIR="$(pwd)"
    cd $WORKDIR
# -- last cd command to go back to the folder we started in

    export PYTHONPATH=$SYNC_ENV

    if [ ${ENABLE_RDB_SIGNAL:-false} ]; then
        export CELERY_RDBSIG=1
    fi

}


# function to start celery
start_celery(){
    local CELERY="celery -b $BROKER_URL -A celery_synchronisation"
    local flowerport=$[SYNC_ID+55000]

    FLOWER_PID="${LOGDIR}/flower.pid"
    FLOWER_OPTS="--max_tasks=500 --port=${flowerport} --log_file_prefix=${LOGDIR}/flower.log --logging=error"
    FLOWER_EXEC="${CELERY} flower ${FLOWER_OPTS}"

    WORKER_PID="${LOGDIR}/worker.pid"
    WORKER_OPTS="--workdir=$LOGDIR -l INFO -E"
    WORKER_OPTS="$WORKER_OPTS --pidfile=${WORKER_PID} -n $SYNC_PARTNER"
    if [ $PURGE_AT_STARTUP ]; then
        WORKER_OPTS="$WORKER_OPTS --purge"
    fi

    if $celeryfg ; then
        echo "Running celery in foregroung ..."
    else
        WORKER_OPTS="$WORKER_OPTS -D -f ${LOGDIR}/worker.log"
        # make the worker go into the background
    fi

    WORKER_EXEC="${CELERY} worker --config=${SYNC_CONFIG} ${WORKER_OPTS}"

    ## start the celery worker and flower monitor
    echo -n "Starting celery flower monitor.."
    $FLOWER_EXEC &
    echo $! > $FLOWER_PID
    sleep 1
    echo ". Started."

    echo -n "Starting celery worker .."
    $WORKER_EXEC

    echo ". Started."
}

celery_can_call(){
    local __retval="$1"
    local can_call='no'
    if [ -n "$(celery -b $BROKER_URL inspect active | head -2 | tail -1|grep -Ee '^ +- empty -$')" ]
    then
        can_call='yes'
    else
        can_call='no'
    fi
    eval $__retval="'$can_call'"
}

celery_call(){
    
    local SYNC_PREFIX="celery -b $BROKER_URL call celery_synchronisation.synchronise"
    local acttocall="$1"
    ${SYNC_PREFIX}_${acttocall} --config=${SYNC_CONFIG}
}


still_running(){
    # uses PS to see if a program is running according to PIDFILE passed in
    # puts a 1 or 0 in the first variable passed in
    local __retval="$1"
    local pidfile="$2"
    if [ -r "$pidfile" ]; then
        if [ -n "$(ps h -p `cat $pidfile`)"]; then
            eval $__retval=true
        else
            eval $__retval=false
        fi
    else
        eval $__retval=false
    fi
}

cycle_all(){
    # SYNC_COMMANDS=" synchronise_push_all synchronise_pull_all synchronise_new"
    local SYNC_COMMANDS=" push_all pull_all new"
    local called=false
    local can_call="no"
    local cyclefile=${LOGDIR}/.is_sync_cycling
    sleep 5
    touch $cyclefile
    echo "Running sync routines every $SYNC_WAIT seconds. Press Ctrl+C to stop.."
    while true; do
        # execute synchronise commands then pause for 3 minutes
        for SYNC_CMD in ${SYNC_COMMANDS}; do
            called=false
            while !($called); do
                if [ -n "$(celery -b $BROKER_URL inspect active | head -2 | tail -1|grep -Ee '^ +- empty -$')" ]
                then
                    if [ -f $cyclefile ]; then
                        celery_call $SYNC_CMD
                        called=true
                    fi
                    sleep 5
                else
                    sleep 10
                fi
            done
        done
        sleep $SYNC_WAIT
    done
    rm $cyclefile

}
# ====================================================================
# cleanup function that shuts down flower and celery worker
cleanup(){
    if [ -n "$(ps h -p `cat ${FLOWER_PID}`)" ]; then
        # flower is indeed running, according to pidfile
        echo -n "shutting down celery-flower monitor .."
        kill -TERM $(cat ${FLOWER_PID})
        echo ". Done."
    fi

    if $celeryfg ; then
        echo -n "almost finished..."
    else
        echo -n "shutting down celery-worker .."
        kill -TERM $(cat ${WORKER_PID})
    fi

    test -f ${FLOWER_PID} && rm $FLOWER_PID
    test -f ${WORKER_PID} && rm $WORKER_PID
    echo ". Done."
}

control_c(){
    echo -n "Ctrl+C detected, "
    cleanup
    exit $?
}

term_signal(){
    echo -n "TERM signal received, "
    cleanup
    exit $?
}

# ====================================================================
trap control_c SIGINT
trap term_signal SIGTERM

# ====================================================================
LONGOPTS="rc:,debug,version,fg,foreground,call:,start,stop,worker,purge"
SHORTOPTS="c:dvfu:a:hp"


#----------------------------
_show_usage(){
    echo "$0 [options]"
    echo ""
    echo "Used to run celery and flower (celery monitor) for synchro engine."
    echo "Options:"
    echo "-c --rc <path>       - path to syncrc file (default ~/.tryton/syncrc)"
    echo "-d --debug           - enable verbose logging to stdout"
    echo "-f --fg --foreground - run celery worker in the foreground"
    echo "-u --call <act>      - call one of the sync actions [pull_all|push_all|new]"
    echo "-p                   - purge the message queue at startup"
    echo "--start              - start synchro. starts celery and does periodic calls"
    echo "--stop               - stop celery worker. only useful for worker only"
    echo "--worker             - run celery only. Don't make periodic calls"
    echo "-a start|stop|worker - same as the previous 3"
    echo "-h                   - show this message"
    echo ""
    exit 0
}
#----------------------------

while getopts "$SHORTOPTS" flag
    do
        echo "the flag is ]$flag["
        case $flag in

            d|debug)
                  debugging=true
                  log "debugging on"
                  ;;
            rc|c)
                conffile="$OPTARG"
                ;;
            f|fg|foreground)
                 celeryfg=true
                 ;;
            u|call)
                celerycallact="$OPTARG"
                ;;
            p|purge)
                PURGE_AT_STARTUP=true
                ;;
            a|act)
                celeryact="$OPTARG"
                ;;
            start|stop|worker)
                celeryact="$flag"
                ;;
            \?)
                echo "invalid option : -$OPTARG" >&2
                exit 1
                ;;
            :)
                echo "option -$OPTARG requires an argument" >&2
                exit 1
                ;;
            h)
                _show_usage
                exit 0
                ;;
        esac
   done
# shift $(( OPTIND - 1 ))  # shift past the last flag or argument

if [ -r "$conffile" ]; then
    log "initializing and reading config file: $conffile"
    minit
else
    echo "$conffile doesn't exist or permission denied"
fi

if [ -n "$celerycallact" ]; then
    celery_call $celerycallact
else
    case $celeryact in
        start)
            start_celery
            cycle_all
        ;;
        worker)
            start_celery
        ;;
        stop)
            cleanup
        ;;
    esac
fi
