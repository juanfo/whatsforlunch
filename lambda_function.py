#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
from botocore.vendored import requests
import datetime
import string


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    
    menu = get_daily_food('hoy')
    speech = get_menu_string(menu, 'hoy')
    speech_output = speech + "¿Qué otro día quieres consultar?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "No te he entendido bien. ¿Qué día quieres consultar?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}

def get_menu():
    r = requests.get('https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit?usp=sharing')
    if r.status_code == 200:
        beginning = 'content="Sheet1'
        begin = r.text.find(beginning) + len(beginning) + 2
        end = r.text.find('"><meta name="google" content="notranslate">')
        text_menu = r.text[begin: end]
        menu_list = []
        for line in text_menu.splitlines():
            menu_list.append(line.split(','))
        return menu_list
    else:
        return None


def get_spanish_day_from_weekday(weekday):
    return ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][weekday]


def get_daily_food(when):
    if when == 'hoy':
        weekday = (datetime.datetime.today() + datetime.timedelta(hours=2)).weekday()
        dia = get_spanish_day_from_weekday(weekday)
    elif when == 'mañana':
        weekday = (datetime.datetime.today() + datetime.timedelta(days=1, hours=2)).weekday()
        dia = get_spanish_day_from_weekday(weekday)
    else:
        dia = when
    print(dia)
    menu = get_menu()
    for day in menu:
        if day[0].lower() == dia.lower():
            ret = []
            for comida in day[1:]:
                ret.append(comida)
            return ret
    return []


def check_food(intent, session):
    when = intent['slots']['when']['value'].lower()
    if 'nada' in when or 'ning' in when:
        speech = 'ok'
    else:
        menu = get_daily_food(when)
        speech = get_menu_string(menu, when)
    
    return build_response({}, build_speechlet_response(
        "Hola", speech, "", True))

def get_menu_string(menu, when):
    if len(menu) == 2:
        speech = when + " tenemos " + menu[0] + " para comer y " + menu[1] + " para cenar."
    elif len(menu) == 1:
        speech = when + " tenemos " + menu[0] + " para comer"
    else:
        speech = when + "No sé que vamos a comer "
    if when.lower() != 'hoy' and when.lower() != 'mañana':
        speech = 'el ' + speech
    return speech
    

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print(session['sessionId'])
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "Tomorrow":
        return check_food(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])
    print(event['session'])
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
