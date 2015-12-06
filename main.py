import flask
from flask import render_template
from flask import request
from flask import url_for
import uuid

import json
import logging

# Date handling 
import arrow # Replacement for datetime, based on moment.js
import datetime # But we still need time
from dateutil import tz  # For interpreting local times


# OAuth2  - Google library implementation for convenience
from oauth2client import client
import httplib2   # used in oauth2 flow

# Google API for services 
from apiclient import discovery

###
# Globals
###
import CONFIG
app = flask.Flask(__name__)

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = CONFIG.GOOGLE_LICENSE_KEY  ## You'll need this
APPLICATION_NAME = 'MeetMe class project'

#############################
#
#  Pages (routed from URLs)
#
#############################
from db import add_proposal, list_proposal, delete_proposal, get_proposal

@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Entering index")
    if 'daterange' not in flask.session:
        init_session_values()
    proposals = list_proposal()
    return render_template('index.html', proposals=proposals)

@app.route("/create", methods=['POST'])
def create():
    app.logger.debug("Create metting")
    daterange = request.form.get('daterange')
    begin_time = request.form.get('begin_time')
    end_time = request.form.get('end_time')
    arr = daterange.split()
    begin = '%s' % (arrow.get('%sT%s' % (arr[0], begin_time), 
            'MM/DD/YYYYTHH:mm').replace(tzinfo=tz.tzlocal()))
    end = '%s' % (arrow.get('%sT%s' % (arr[2], end_time),
            'MM/DD/YYYYTHH:mm').replace(tzinfo=tz.tzlocal()))
    add_proposal(begin, end)
    return flask.redirect(flask.url_for('index'))

@app.route("/delete")
def delete():
    key = request.args.get('key')
    delete_proposal(key)
    return flask.redirect(flask.url_for('index'))

@app.route("/proposal")
def proposal():
    ## We'll need authorization to list calendars 
    ## I wanted to put what follows into a function, but had
    ## to pull it back here because the redirect has to be a
    ## 'return' 
    if request.args.get('key'):
        flask.session['key'] = request.args.get('key')
    key = flask.session.get('key')
    if not key:
        return flask.redirect(flask.url_for('index'))
    proposal = get_proposal(key)
    if not proposal:
        return flask.redirect(flask.url_for('index'))
    
    credentials = valid_credentials()
    if not credentials:
      app.logger.debug("Redirecting to authorization")
      return flask.redirect(flask.url_for('oauth2callback'))

    gcal_service = get_gcal_service(credentials)
    app.logger.debug("Returned from get_gcal_service")
    events = list_events(gcal_service, proposal['begin'], proposal['end'])

    proposal['begin'] = '%s' % arrow.get(proposal['begin']).format('MM/DD/YYYYTHH:mm')
    proposal['end'] = '%s' % arrow.get(proposal['end']).format('MM/DD/YYYYTHH:mm')
    proposal['id'] = '%s' % proposal['_id']
    daterange = {
        'begin': proposal['begin'],
        'end': proposal['begin'],
    }
    free_times = split_times(daterange, events)
    return render_template('proposal.html', proposal=proposal, free_times=free_times, events=events)

####
#
#  Google calendar authorization:
#      Returns us to the main /choose screen after inserting
#      the calendar_service object in the session state.  May
#      redirect to OAuth server first, and may take multiple
#      trips through the oauth2 callback function.
#
#  Protocol for use ON EACH REQUEST: 
#     First, check for valid credentials
#     If we don't have valid credentials
#         Get credentials (jump to the oauth2 protocol)
#         (redirects back to /choose, this time with credentials)
#     If we do have valid credentials
#         Get the service object
#
#  The final result of successful authorization is a 'service'
#  object.  We use a 'service' object to actually retrieve data
#  from the Google services. Service objects are NOT serializable ---
#  we can't stash one in a cookie.  Instead, on each request we
#  get a fresh serivce object from our credentials, which are
#  serializable. 
#
#  Note that after authorization we always redirect to /choose;
#  If this is unsatisfactory, we'll need a session variable to use
#  as a 'continuation' or 'return address' to use instead. 
#
####

def valid_credentials():
    """
    Returns OAuth2 credentials if we have valid
    credentials in the session.  This is a 'truthy' value.
    Return None if we don't have credentials, or if they
    have expired or are otherwise invalid.  This is a 'falsy' value. 
    """
    if 'credentials' not in flask.session:
      return None

    credentials = client.OAuth2Credentials.from_json(
        flask.session['credentials'])

    if (credentials.invalid or
        credentials.access_token_expired):
      return None
    return credentials


def get_gcal_service(credentials):
  """
  We need a Google calendar 'service' object to obtain
  list of calendars, busy times, etc.  This requires
  authorization. If authorization is already in effect,
  we'll just return with the authorization. Otherwise,
  control flow will be interrupted by authorization, and we'll
  end up redirected back to /choose *without a service object*.
  Then the second call will succeed without additional authorization.
  """
  app.logger.debug("Entering get_gcal_service")
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('calendar', 'v3', http=http_auth)
  app.logger.debug("Returning service")
  return service

@app.route('/oauth2callback')
def oauth2callback():
  """
  The 'flow' has this one place to call back to.  We'll enter here
  more than once as steps in the flow are completed, and need to keep
  track of how far we've gotten. The first time we'll do the first
  step, the second time we'll skip the first step and do the second,
  and so on.
  """
  app.logger.debug("Entering oauth2callback")
  flow =  client.flow_from_clientsecrets(
      CLIENT_SECRET_FILE,
      scope= SCOPES,
      redirect_uri=flask.url_for('oauth2callback', _external=True))
  ## Note we are *not* redirecting above.  We are noting *where*
  ## we will redirect to, which is this function. 
  
  ## The *second* time we enter here, it's a callback 
  ## with 'code' set in the URL parameter.  If we don't
  ## see that, it must be the first time through, so we
  ## need to do step 1. 
  app.logger.debug("Got flow")
  if 'code' not in flask.request.args:
    app.logger.debug("Code not in flask.request.args")
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
    ## This will redirect back here, but the second time through
    ## we'll have the 'code' parameter set
  else:
    ## It's the second time through ... we can tell because
    ## we got the 'code' argument in the URL.
    app.logger.debug("Code was in flask.request.args")
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    ## Now I can build the service and execute the query,
    ## but for the moment I'll just log it and go back to
    ## the main screen
    app.logger.debug("Got credentials")
    return flask.redirect(flask.url_for('proposal'))

#####
#
#  Option setting:  Buttons or forms that add some
#     information into session state.  Don't do the
#     computation here; use of the information might
#     depend on what other information we have.
#   Setting an option sends us back to the main display
#      page, where we may put the new information to use. 
#
#####

@app.route('/set', methods=['POST'])
def set():
    """
    User chose a date range with the bootstrap daterange
    widget.
    """
    app.logger.debug("Entering set")
    # set calid and datetime
    calid = request.form.get('calid')
    daterange = request.form.get('daterange')
    begin_time = request.form.get('begin_time')
    end_time = request.form.get('end_time')

    flask.session['calid'] = calid
    flask.session['daterange'] = daterange
    flask.session["begin_time"] = begin_time
    flask.session["end_time"] = end_time
    cal_timerange()
    app.logger.debug("Set calid=%s, daterange=%s, begin_time=%s', end_time=%s",
            calid, daterange, begin_time, end_time)
    
    return flask.redirect(flask.url_for("choose"))

####
#
#   Initialize session variables 
#
####

def init_session_values():
    """
    Start with some reasonable defaults for date and time ranges.
    Note this must be run in app context ... can't call from main. 
    """
    # Default date span = tomorrow to 1 week from now
    now = arrow.now('local')
    tomorrow = now.replace(days=+1)
    nextweek = now.replace(days=+7)
    flask.session["daterange"] = "{} - {}".format(
        tomorrow.format("MM/DD/YYYY"),
        nextweek.format("MM/DD/YYYY"))
    # Default time span each day, 8 to 5
    #flask.session["begin_time"] = interpret_time("9am")
    #flask.session["end_time"] = interpret_time("5pm")
    flask.session["begin_time"] = "09:00"
    flask.session["end_time"] = "17:00"
    cal_timerange()

def interpret_time( text ):
    """
    Read time in a human-compatible format and
    interpret as ISO format with local timezone.
    May throw exception if time can't be interpreted. In that
    case it will also flash a message explaining accepted formats.
    """
    app.logger.debug("Decoding time '{}'".format(text))
    time_formats = ["ha", "h:mma",  "h:mm a", "H:mm"]
    try: 
        as_arrow = arrow.get(text, time_formats).replace(tzinfo=tz.tzlocal())
        app.logger.debug("Succeeded interpreting time")
    except:
        app.logger.debug("Failed to interpret time")
        flask.flash("Time '{}' didn't match accepted formats 13:30 or 1:30pm"
              .format(text))
        raise
    return as_arrow.isoformat()

def interpret_date( text ):
    """
    Convert text of date to ISO format used internally,
    with the local time zone.
    """
    try:
      as_arrow = arrow.get(text, "MM/DD/YYYY").replace(
          tzinfo=tz.tzlocal())
    except:
        flask.flash("Date '{}' didn't fit expected format 12/31/2001")
        raise
    return as_arrow.isoformat()

def next_day(isotext):
    """
    ISO date + 1 day (used in query to Google calendar)
    """
    as_arrow = arrow.get(isotext)
    return as_arrow.replace(days=+1).isoformat()

####
#
#  Functions (NOT pages) that return some information
#
####
  
def list_events(service, begin, end):
    """
    Given a google 'service' object, return a list of
    calendars.  Each calendar is represented by a dict, so that
    it can be stored in the session object and converted to
    json for cookies. The returned list is sorted to have
    the primary calendar first, and selected (that is, displayed in
    Google Calendars web app) calendars before unselected calendars.
    """
    app.logger.debug("Entering list_calendars")  
    calendar_list = service.calendarList().list().execute()["items"]
    result = []
    for cal in calendar_list:
        id = cal["id"]
        events = service.events().list(calendarId=id, timeMin=begin,
                timeMax=end).execute()['items']
        for event in events:
            if not event.get('start') or not event['start'].get('dateTime'):
                continue
            result.append({
                "summary": event["summary"],
                "start": '%s' % arrow.get(event["start"]["dateTime"]).format('MM/DD/YYYYTHH:mm'),
                "end": '%s' % arrow.get(event["end"]["dateTime"]).format('MM/DD/YYYYTHH:mm'),
            })
    result.sort(key=lambda x: x["start"])
    return result

def cal_timerange():
    daterange = flask.session['daterange']
    begin_time = flask.session['begin_time']
    end_time = flask.session['end_time']
    arr = daterange.split()
    flask.session['begin'] = '%s' % (arrow.get('%sT%s' % (arr[0], begin_time), 
            'MM/DD/YYYYTHH:mm').replace(tzinfo=tz.tzlocal()))
    flask.session['end'] = '%s' % (arrow.get('%sT%s' % (arr[2], end_time),
            'MM/DD/YYYYTHH:mm').replace(tzinfo=tz.tzlocal()))

def split_times(daterange, events):
    """
    split daterange with events
    """
    begin = arrow.get(daterange['begin'], 'MM/DD/YYYYTHH:mm')
    end = arrow.get(daterange['end'], 'MM/DD/YYYYTHH:mm')
    free_times = []
    for event in events:
        st = arrow.get(event["start"], 'MM/DD/YYYYTHH:mm')
        et = arrow.get(event["end"], 'MM/DD/YYYYTHH:mm')
        if begin < et:
            if begin < st:
                free_times.append('%s - %s' %(begin.format('MM/DD/YYYYTHH:mm'),
                    st.format('MM/DD/YYYYTHH:mm')))
            begin = et
    if begin < end:
        free_times.append('%s - %s' %(begin.format('MM/DD/YYYYTHH:mm'),
            end.format('MM/DD/YYYYTHH:mm')))
    return free_times

def cal_sort_key( cal ):
    """
    Sort key for the list of calendars:  primary calendar first,
    then other selected calendars, then unselected calendars.
    (" " sorts before "X", and tuples are compared piecewise)
    """
    if cal["selected"]:
       selected_key = " "
    else:
       selected_key = "X"
    if cal["primary"]:
       primary_key = " "
    else:
       primary_key = "X"
    return (primary_key, selected_key, cal["summary"])


#################
#
# Functions used within the templates
#
#################

@app.template_filter( 'fmtdate' )
def format_arrow_date( date ):
    try: 
        normal = arrow.get( date )
        return normal.format("ddd MM/DD/YYYY")
    except:
        return "(bad date)"

@app.template_filter( 'fmttime' )
def format_arrow_time( time ):
    try:
        normal = arrow.get( time )
        return normal.format("HH:mm")
    except:
        return "(bad time)"
    
#############


if __name__ == "__main__":
  # App is created above so that it will
  # exist whether this is 'main' or not
  # (e.g., if we are running in a CGI script)

  app.secret_key = str(uuid.uuid4())  
  app.debug=CONFIG.DEBUG
  app.logger.setLevel(logging.DEBUG)
  # We run on localhost only if debugging,
  # otherwise accessible to world
  if CONFIG.DEBUG:
    # Reachable only from the same computer
    app.run(port=CONFIG.PORT,host="0.0.0.0")
  else:
    # Reachable from anywhere 
    app.run(port=CONFIG.PORT,host="0.0.0.0")
    
