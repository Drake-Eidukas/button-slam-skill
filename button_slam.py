""" Main intent handler for the button slam alexa skill
"""
from flask import Flask, render_template
from flask_ask import Ask, session, statement, question
from bs4 import BeautifulSoup as bs
import requests
# import boto3
# import logging

app = Flask(__name__)
ask = Ask(app)
# log = logging.getLogger()

MAIN_MENU_STATE = 'main_menu'
DILEMMA_STATE = 'dilemma'
# STAT_STATE = 'stat'

QUESTION_STATEMENT = 'question'
QUESTION_STATEMENT_REPROMPT = 'question_reprompt'
STATS_STATEMENT = 'stats'
STATS_STATEMENT_REPROMPT = 'stats_reprompt'
STARTING_STATEMENT = 'starting_statement'
STARTING_STATEMENT_REPROMPT = 'starting_statement_reprompt'
EXPLAIN_STATEMENT = 'explain_the_game'
EXPLAIN_STATEMENT_REPROMPT = 'explain_the_game_reprompt'
DONE_STATEMENT = 'done_playing'

@ask.launch
def launched():
    """ When the skill is first launched, present the user with the
    welcome text and ask them to play a game.
    """
    session.attributes['state'] = MAIN_MENU_STATE

    welcome_text = render_template(STARTING_STATEMENT)
    welcome_text_reprompt = render_template(STARTING_STATEMENT_REPROMPT)
    return question(welcome_text).reprompt(welcome_text_reprompt)

@ask.intent('AMAZON.HelpIntent')
def help_user():
    """ If the user asks for help at some point during the game, explain the game
    and return them to the starting menu
    """
    session.attributes['state'] = MAIN_MENU_STATE

    help_text = render_template(EXPLAIN_STATEMENT)
    help_text_reprompt = render_template(EXPLAIN_STATEMENT_REPROMPT)
    return question(help_text).reprompt(help_text_reprompt)

@ask.intent('AMAZON.StopIntent')
@ask.intent('AMAZON.CancelIntent')
def quit_session():
    """
    Quit out of the current session if the user asks to cancel or stop during
    the interaction.
    """
    session.attributes['state'] = MAIN_MENU_STATE
    bye_text = render_template('done_playing')
    return statement(bye_text)

@ask.intent('AMAZON.YesIntent')
def yes():
    """ If the user sends a yes intent, there are two possible meanings--
    Either the user is saying yes, they will hit the button, or the user is saying
    yes, I would like to play another game despite that not being part of what
    alexa is asking for. We handle this by keeping track of the current state of the
    session using the session attributes.
    """
    if session.attributes['state'] != DILEMMA_STATE:
        # If we haven't just asked them a dilemma, then ask them one!
        return ask_question()
    else:
        # If we just asked them a dilemma, then handle that correctly.
        return answer_question(True)

@ask.intent('AMAZON.NoIntent')
def no():
    """ If the user sends a no intent, there are two possible meanings--
    Either the user is saying no, the will not hit the button, or the user is saying
    no, I would not like to play another game despite that not being part of what alexa
    is asking for. We handle this by keeping track of the current state of the session
    using the session attributes.
    """
    if session.attributes['state'] != DILEMMA_STATE:
        # If we haven't just asked them a dilemma, then quit the session!
        return quit_session()
    else:
        # If we just asked them a dilemma, then handle that correctly.
        return answer_question(False)

@ask.intent('NewQuestionIntent')
def ask_question():
    """ Fetch a new question from the api, and propose it to the user.
    """
    session.attributes['state'] = DILEMMA_STATE

    random_question_data = get_main_webpage_data()
    pro_text = random_question_data['pro_text']
    con_text = random_question_data['con_text']

    session.attributes['id'] = random_question_data['id']
    session.attributes['pro_text'] = pro_text
    session.attributes['con_text'] = con_text

    question_text = render_template(QUESTION_STATEMENT, pro=pro_text, con=con_text)
    question_text_reprompt = render_template(QUESTION_STATEMENT_REPROMPT)

    return question(question_text).reprompt(question_text_reprompt)

def answer_question(response):
    """ Answer the question of whether or not to slam the button,
    and respond with stats about how many people slammed the button!
    """
    session.attributes['state'] = MAIN_MENU_STATE
    question_id = session.attributes['id']

    stats = get_response_stats_data(question_id, response)
    pro_count = stats['pro_count']
    con_count = stats['con_count']
    pro_percent = stats['pro_percent']
    con_percent = stats['con_percent']

    stat_text = render_template(STATS_STATEMENT,
                                pro_count=pro_count,
                                con_count=con_count,
                                pro_percent=pro_percent,
                                con_percent=con_percent)

    stat_text_reprompt = render_template(STATS_STATEMENT_REPROMPT)

    return question(stat_text).reprompt(stat_text_reprompt)

@ask.session_ended
def session_ended():
    """ When the user's session ends, send this response to the AVS
    """
    return "", 200

class InvalidIndex(Exception):
    """ Exception to throw if the given question id is invalid.
    """
    pass

def get_webpage(webpage):
    """ Given a url, return the text of the webpage behind that url.
    """
    return requests.get(
        webpage,
        headers={
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 ' +
                          '(KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        }
    ).text

def get_stat_webpage_data(question_id):
    """ Given the id of a question, fetch the stats of that given question.
    """
    webpage = 'https://willyoupressthebutton.com/{0}/stats'.format(question_id)
    webpage_content = get_webpage(webpage)

    soup = bs(webpage_content, 'html.parser')

    main_container = soup.find(id='maincontainer')

    if main_container is None:
        raise InvalidIndex({
            "message":"No question found with that index",
            "index": question_id
        })

    stats = [stat for stat in [a for a in main_container.find(id='statsBar').children][1].children]

    did_press = stats[1].getText()
    did_press_count = int(did_press.split()[0])

    didnt_press = stats[3].getText()
    didnt_press_count = int(didnt_press.split()[0])

    dilemma = [a for a in main_container.find(id='dilemma').children]
    pro = dilemma[1].getText().strip()
    con = dilemma[5].getText().strip()

    return {
        'link': webpage,
        'index': question_id,
        'pro': pro,
        'con': con,
        'did_press_count': did_press_count,
        'didnt_press_count': didnt_press_count
    }

def get_main_webpage_data():
    """ Goes to the main page of willyoupressthebutton.com, 
    and scrapes to figure out the given question, stats, and question id.
    """
    webpage = 'https://willyoupressthebutton.com'
    webpage_content = get_webpage(webpage)
    
    soup = bs(webpage_content, 'html.parser')
    
    main_container = soup.find(id='maincontainer')
    
    yes_button_container = main_container.find(id='yesbtn')
    question_id = int(yes_button_container['href'].split('/')[1])
    
    pro_container = main_container.find(id='cond')
    pro_text = pro_container.getText().strip()
    
    con_container = main_container.find(id='res')
    con_text = con_container.getText().strip()
    
    return {
        'id': question_id,
        'pro_text': pro_text,
        'con_text': con_text
    }

def get_response_stats_data(question_id, user_response):
    """ Given a question ID and the user's response, notify the website,
    and get the most updated stats about the question.
    """
    webpage = 'https://willyoupressthebutton.com/{0}/'.format(question_id)
    if user_response:
        webpage += 'yes'
    else:
        webpage += 'no'

    webpage_content = get_webpage(webpage)

    soup = bs(webpage_content, 'html.parser')

    main_container = soup.find(id='maincontainer')

    if main_container is None:
        raise InvalidIndex({
            "message":"No question found with that index",
            "index": question_id
        })

    stats = [stat for stat in [a for a in main_container.find(id='statsBar').children][1].children]

    did_press = stats[1].getText()
    did_press_count = int(did_press.split()[0])
    did_press_percent = int(did_press[did_press.index('(') + 1: did_press.index(')') - 1])

    didnt_press = stats[3].getText()
    didnt_press_count = int(didnt_press.split()[0])
    didnt_press_percent = 100 - did_press_percent

    return {
        'id': question_id,
        'pro_count': did_press_count,
        'con_count': didnt_press_count,
        'pro_percent': did_press_percent,
        'con_percent': didnt_press_percent
    }
if __name__ == '__main__':
    app.run(debug=True)
