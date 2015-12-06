import arrow

def split_times(daterange, events):
    """
    split daterange with events, like the split_time from main
    but for test, we get the information from arguments, not from flask.session
    daterange is a dict like this
    {
        'begin': '11/20/2015T09:00',
        'end':   '12/20/2015T18:00',
    }
    events is a array like this, events must sorted by start
    [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '11/20/2015T13:00', 'end': '11/20/2015T14:00'},
        {'start': '12/20/2015T13:00', 'end': '12/20/2015T14:30'},
    ]
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

def test1():
    """
    The first one is a samplest test to test the function work right.
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T10:30 - 11/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test2():
    """
    The second one test two adjacent events
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '11/20/2015T10:30', 'end': '11/20/2015T11:00'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T11:00 - 11/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test3():
    """
    The third one test multi non-adjacent events
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '11/20/2015T11:00', 'end': '11/20/2015T11:30'},
        {'start': '11/20/2015T12:00', 'end': '11/20/2015T12:30'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T10:30 - 11/20/2015T11:00', 
        '11/20/2015T11:30 - 11/20/2015T12:00', 
        '11/20/2015T12:30 - 11/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test4():
    """
    The 4th one test multi non-adjacent events
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '11/20/2015T11:00', 'end': '11/20/2015T11:30'},
        {'start': '11/20/2015T12:00', 'end': '11/20/2015T12:30'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T10:30 - 11/20/2015T11:00', 
        '11/20/2015T11:30 - 11/20/2015T12:00', 
        '11/20/2015T12:30 - 11/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test5():
    """
    The 5th one test the first event at the begin of daterange
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T09:00', 'end': '11/20/2015T10:00'},
        {'start': '11/20/2015T11:00', 'end': '11/20/2015T11:30'},
    ]
    result = [
        '11/20/2015T10:00 - 11/20/2015T11:00', 
        '11/20/2015T11:30 - 11/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test6():
    """
    The 6th one test the last event at the end of daterange
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '11/20/2015T16:00', 'end': '11/20/2015T17:00'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T10:30 - 11/20/2015T16:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test7():
    """
    The 7th one test the first event and the last event out of the bound of daterange
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T08:00', 'end': '11/20/2015T09:30'},
        {'start': '11/20/2015T16:30', 'end': '11/20/2015T17:30'},
    ]
    result = [
        '11/20/2015T09:30 - 11/20/2015T16:30', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test8():
    """
    The 8th one test no events
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '11/20/2015T17:00',
    }
    events = [
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test9():
    """
    The 9th one test daterange with cross date
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '12/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '12/20/2015T10:00', 'end': '12/20/2015T10:30'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T10:30 - 12/20/2015T10:00', 
        '12/20/2015T10:30 - 12/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

def test10():
    """
    The 10th one test daterange with cross date, and events cross date
    """
    daterange = {
        'begin': '11/20/2015T09:00',
        'end':   '12/20/2015T17:00',
    }
    events = [
        {'start': '11/20/2015T10:00', 'end': '11/20/2015T10:30'},
        {'start': '11/20/2015T23:30', 'end': '12/20/2015T00:30'},
        {'start': '12/20/2015T10:00', 'end': '12/20/2015T10:30'},
    ]
    result = [
        '11/20/2015T09:00 - 11/20/2015T10:00', 
        '11/20/2015T10:30 - 11/20/2015T23:30', 
        '12/20/2015T00:30 - 12/20/2015T10:00', 
        '12/20/2015T10:30 - 12/20/2015T17:00', 
    ]
    free_times = split_times(daterange, events)
    assert(result == free_times)

if __name__ == '__main__':
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
    test8()
    test9()
    test10()

