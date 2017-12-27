from flask import Flask, render_template
from flask_ask import Ask, request, session, version, statement, question

app = Flask(__name__)
ask = Ask(app)
log = logging.getLogger()

MAIN_MENU_STATE = 'main_menu'
DILEMMA_STATE = 'dilemma'


STARTING_STATEMENT = 'starting_statement'
STARTING_STATEMENT_REPROMPT = 'starting_statement_reprompt'
EXPLAIN_STATEMENT = 'explain_the_game'
EXPLAIN_STATEMENT_REPROMPT = 'explain_the_game_reprompt'

@ask.launch
def launched():
    """ When the skill is first launched, present the user with the 
    welcome text and ask them to play a game. 
    """
    welcome_text = render_template(STARTING_STATEMENT)
    welcome_text_reprompt = render_template(STARTING_STATEMENT_REPROMPT)
    return question(welcome_text).reprompt(welcome_text_reprompt)

@ask.intent('AMAZON.HelpIntent')
def help():
    """ If the user asks for help at some point during the game, explain the game
    and return them to the starting menu
    """
    session.attributes['state'] = 

    help_text = render_template(EXPLAIN_STATEMENT)
    return question(help_text).reprompt(EXPLAIN_STATEMENT_REPROMPT)

@ask.intent('AMAZON.StopIntent')
@ask.intent('AMAZON.CancelIntent')
def quit():
    """
    Quit out of the current session if the user asks to cancel or stop during
    the interaction. 
    """
    bye_text = render_template('done_playing')
    return statement(bye_text)

@ask.intent('AMAZON.YesIntent')
def yes(): 
    """ If the user sends a yes intent, there are two possible meanings--
    Either the user is saying yes, they will hit the button, or the user is saying
    yes, I would like to play another game despite that not being part of what alexa is asking for.
    We handle this by keeping track of the current state of the session using the session attributes. 
    """
    if session.attributes['state'] != 'question': 
        # If we haven't just asked them a dilemma, then ask them one!
        pass
    else: 
        # If we just asked them a dilemma, then handle that correctly.
        pass

@ask.intent('AMAZON.NoIntent')
def no():
    """ If the user sends a no intent, there are two possible meanings--
    Either the user is saying no, the will not hit the button, or the user is saying 
    no, I would not like to play another game despite that not being part of what alexa is asking for.
    We handle this by keeping track of the current state of the session using the session attributes.
    """
    if session.attributes['state'] != 'question': 
        # If we haven't just asked them a dilemma, then quit the session!
        pass
    else: 
        # If we just asked them a dilemma, then handle that correctly.
        return quit()

@ask.session_ended
def session_ended():
    return "", 200

if __name__ == '__main__':
    app.run(debug=True)
