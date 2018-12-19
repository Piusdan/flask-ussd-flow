import logging
from functools import wraps

from flask import g, request, current_app

from . import ussd_logger


class USSDException(Exception):
    pass


def manage_flows():
    pass


class Status:
    """
    Manages users status
    """
    not_registered = 1
    registered = 2
    pending = 3


class Flow:
    """
    manages screen flows
    """
    registration = 'user_registration'
    main = "main"


class Callback:
    """
    Manage allowed callback types
    """
    function = "func"
    http = "http"
    asynchronous = "async"


class ScreenValidationTypes:
    regex = 'regex'
    list = 'list'


def ussd_view(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload = request.values
        g.phoneNumber = payload['phoneNumber']
        g.sessionId = payload['sessionId']
        g.serviceCode = payload['serviceCode']
        g.ussd_text = payload['text']
        user_input = payload['text'].split('*')[-1]

        response = f(*args, **kwargs)
        flow_name = response.get('flow_name', 'main')

        all_screens = current_app.ussd_flow.get_screens(flow_name)

        # prev_screen, current_screen = current_app.ussd_flow.get_screen(all_screens=all_screens, user_inputs=g.ussd_text)
        previous_screen, current_screen = current_app.ussd_flow.get_screen(all_screens=all_screens, user_inputs=g.ussd_text)

        g.ussd_state = dict(previous_screen=previous_screen, current_screen=current_screen, user_input=user_input)

        if previous_screen is not None:
            current_app.ussd_flow.execute_callback(sessionId=g.sessionId, phoneNumber=g.phoneNumber, user_input=user_input, screen=previous_screen)
        else:
            ussd_logger.debug('Skipping callback')

        response = current_app.ussd_flow.render(current_screen)

        return response

    return decorated_function
