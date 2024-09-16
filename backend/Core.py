# Import gevent and patch all to ensure that the standard library works in a non-blocking way
from gevent import monkey
monkey.patch_all()

import openai
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from datetime import datetime
import numpy
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO with gevent async mode
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="http://localhost:8000")

# Global Variables
turn = 1
conversation_history = []
clients = {'plaintiff': None, 'defendant': None}  # Store socket connections
plaintiff_last_prices = []  # Track last 3 responses for plaintiff
defendant_last_prices = []  # Track last 3 responses for defendant
common_price_reached = False  # Track whether a common price has been agreed
plaintiff_agrees = False  # Track if plaintiff agrees to common price
defendant_agrees = False  # Track if defendant agrees to common price
plaintiff_name = ""
defendant_name = ""
plaintiff_profile = {}
defendant_profile = {}
plaintiff_question_index = 0
defendant_question_index = 0
courtCostTotal = 20 * 380 + 1500  # Court cost calculation: 20 hours * $380 + $1500

# Initial questions
initial_questions = {
    "plaintiff": [
        "What kind of dispute is this?",
        "How much are you seeking in damages?",
        "How much do you earn per hour?",
        "What's the lowest payout you would take?"
    ],
    "defendant": [
        #"How much are you seeking in damages?",
        #"Do you confirm that the plaintiff is seeking damages?",
        "How much do you earn per hour?",
        "How much would you pay to avoid this?",
        "What's the max you would pay to the plaintiff?"
    ]
}

# Updated Directions for the AI Mediator
directions = """
...  # (rest of directions here)
"""

# Helper function to calculate court costs and opportunity cost
def calculate_costs(user_type):
    global courtCostTotal

    if user_type == "plaintiff":
        wage = float(plaintiff_profile.get('earnings_per_hour', 0))
        lowest_payout = float(plaintiff_profile.get('lowest_payout', 0))
        opportunityCost = wage * 20  # Time they won't be able to work
        adjusted_lowest_payout = lowest_payout - courtCostTotal
        return {"courtCostTotal": courtCostTotal, "opportunityCost": opportunityCost, "adjusted_lowest_payout": adjusted_lowest_payout}

    elif user_type == "defendant":
        wage = float(defendant_profile.get('earnings_per_hour', 0))
        max_payment = float(defendant_profile.get('max_payment', 0))
        opportunityCost = wage * 20  # Time they won't be able to work
        adjusted_max_payment = max_payment - courtCostTotal
        return {"courtCostTotal": courtCostTotal, "opportunityCost": opportunityCost, "adjusted_max_payment": adjusted_max_payment}


def check_same_last_three(prices):
    return len(prices) >= 3 and prices[-1] == prices[-2] == prices[-3]


def check_common_price():
    global plaintiff_profile, defendant_profile
    if 'lowest_payout' not in plaintiff_profile or 'max_payment' not in defendant_profile:
        return False  # Ensure both values are present before comparison

    plaintiff_price = float(plaintiff_profile['lowest_payout'])
    defendant_price = float(defendant_profile['max_payment'])

    return plaintiff_price <= defendant_price


@socketio.on('confirm_common_price')
def confirm_common_price(data):
    global common_price_reached, plaintiff_agrees, defendant_agrees, turn

    user_type = data['user_type']  # 'plaintiff' or 'defendant'
    user_agrees = data['agrees']  # True or False

    if user_type == 'plaintiff':
        plaintiff_agrees = user_agrees
    elif user_type == 'defendant':
        defendant_agrees = user_agrees

    # Check if both parties agree to the common price
    if plaintiff_agrees and defendant_agrees:
        # Both agreed, mediation ends
        common_price_reached = True
        generate_log("Mediation successfully concluded.")
        emit('ai_response', {'ai_response': "Both parties have agreed to the common price. Mediation successfully concluded."}, broadcast=True)
        return
    elif plaintiff_agrees or defendant_agrees:
        # One party agreed, continue to wait for the other party's response
        emit('ai_response', {'ai_response': f"Waiting for the other party to confirm the common price."})
        return
    else:
        # If one or both disagree, continue mediation
        common_price_reached = False
        emit('ai_response', {'ai_response': "One or both parties have disagreed. Continuing mediation."}, broadcast=True)
        return


# WebSocket to handle communication between both parties
@socketio.on('connect')
def handle_connect():
    emit('response', {'message': 'Connected to the Mediation Server'})


# WebSocket to register the user (plaintiff or defendant)
@socketio.on('register_user')
def register_user(data):
    global clients, plaintiff_name, defendant_name
    user_type = data['user_type']  # 'plaintiff' or 'defendant'
    name = data['name']  # User's name

    # Log the registration attempt
    print(f"Registering {user_type} with name {name}")

    # Register the connection for the specific user
    if user_type == 'plaintiff':
        clients['plaintiff'] = request.sid
        plaintiff_name = name
        emit('next_question', {'next_question': initial_questions['plaintiff'][plaintiff_question_index]}, to=clients['plaintiff'])
        print(f"Plaintiff registered with SID {request.sid}")
        
    elif user_type == 'defendant':
        clients['defendant'] = request.sid
        defendant_name = name
        emit('next_question', {'next_question': initial_questions['defendant'][defendant_question_index]}, to=clients['defendant'])
        print(f"Defendant registered with SID {request.sid}")

    # Debugging: Print the clients dictionary
    print(f"Clients after registration: {clients}")


# WebSocket to ask initial questions and collect responses

@socketio.on('initial_questions')
def handle_initial_questions(data):
    global plaintiff_question_index, defendant_question_index, plaintiff_profile, defendant_profile

    user_type = data['user_type']  # 'plaintiff' or 'defendant'
    answer = data['answer']  # Answer to the last question

    if user_type == "plaintiff":
        question_index = plaintiff_question_index
        if question_index < len(initial_questions["plaintiff"]):
            # Log the question for debugging
            print(f"Asking plaintiff question {plaintiff_question_index}: {initial_questions['plaintiff'][plaintiff_question_index]}")
            
            # Store the plaintiff's answer in the profile
            if question_index == 0:
                plaintiff_profile['dispute_type'] = answer
            elif question_index == 1:
                plaintiff_profile['damages_seeking'] = answer
            elif question_index == 2:
                plaintiff_profile['earnings_per_hour'] = answer
            elif question_index == 3:
                plaintiff_profile['lowest_payout'] = answer

            # Increment the question index for the plaintiff
            plaintiff_question_index += 1

            # Ask the next question if any are remaining
            if plaintiff_question_index < len(initial_questions["plaintiff"]):
                next_question = initial_questions['plaintiff'][plaintiff_question_index]
                emit('next_question', {'next_question': next_question}, to=clients['plaintiff'])
            else:
                emit('message', {'message': "Plaintiff questions completed."}, to=clients['plaintiff'])

    elif user_type == "defendant":
        question_index = defendant_question_index
        if question_index < len(initial_questions["defendant"]):
            # Log the question for debugging
            print(f"Asking defendant question {defendant_question_index}: {initial_questions['defendant'][defendant_question_index]}")

            # Store the defendant's answer in the profile
            if question_index == 0:
                defendant_profile['earnings_per_hour'] = answer
            elif question_index == 1:
                defendant_profile['pay_to_avoid'] = answer
            elif question_index == 2:
                defendant_profile['max_payment'] = answer

            # Increment the question index for the defendant
            defendant_question_index += 1

            # Ask the next question if any are remaining
            if defendant_question_index < len(initial_questions["defendant"]):
                next_question = initial_questions['defendant'][defendant_question_index]
                emit('next_question', {'next_question': next_question}, to=clients['defendant'])
            else:
                emit('message', {'message': "Defendant questions completed."}, to=clients['defendant'])

    # Check if both parties have completed their questions
    if plaintiff_question_index >= len(initial_questions["plaintiff"]) and defendant_question_index >= len(initial_questions["defendant"]):
        # Both parties have completed their questions, ready for mediation
        emit('ready_for_mediation', {'message': "Both parties have completed the initial questions. You can now begin mediation."}, broadcast=True)

        # Automatically start the mediation after both parties have completed questions
        emit('ai_response', {
            'ai_response': "Mediation is now starting. Plaintiff, please make your first offer.",
        }, to=clients['plaintiff'])

@socketio.on('mediate')
def handle_mediate(data):
    global turn, conversation_history, clients, plaintiff_last_prices, defendant_last_prices, common_price_reached

    plaintiff_name = data['plaintiff_name']
    defendant_name = data['defendant_name']
    user_input = data['user_input']

    # Ensure both profiles are fully populated before starting mediation
    if 'lowest_payout' not in plaintiff_profile or 'max_payment' not in defendant_profile:
        emit('ai_response', {'ai_response': 'Both parties need to finish answering questions before mediation can begin.'})
        return

    # Track which user is currently responding and whose turn it is
    if turn == 1:
        current_user = plaintiff_name
        other_user = defendant_name
        current_user_sid = clients['plaintiff']
        current_last_prices = plaintiff_last_prices
    else:
        current_user = defendant_name
        other_user = plaintiff_name
        current_user_sid = clients['defendant']
        current_last_prices = defendant_last_prices

    # Add the current user's input to the conversation history with author tracking
    conversation_history.append({"author": current_user, "message": user_input})

    # Store the user's latest price (we assume 'price' means damages or offer mentioned)
    current_last_prices.append(user_input)

    # Check if the user's last 3 responses were the same
    if check_same_last_three(current_last_prices):
        costs = calculate_costs("plaintiff" if current_user == plaintiff_name else "defendant")
        message = f"{current_user} has not changed their asking price for three turns. We appreciate both parties' participation, but we will now end the mediation.\n" \
                  f"Court costs total: ${costs['courtCostTotal']}. Estimated opportunity cost for {current_user}: ${costs['opportunityCost']}. Time commitment: 1 year."
        conversation_history.append({"author": "mediator", "message": message})
        generate_log(message)
        emit('ai_response', {'ai_response': message}, broadcast=True)
        return

    if check_common_price():
        emit('ai_response', {'ai_response': "A common price has been reached. Both parties must confirm this price to conclude the mediation. Please respond with either 'agree' or 'disagree'."}, broadcast=True)
        return

    # Prepare the prompt for GPT-4 based on the conversation history and costs
    # Prepare the prompt for GPT-4 based on the conversation history and costs
    history = "\n".join([f"{entry['author']}: {entry['message']}" for entry in conversation_history])
    costs = calculate_costs("plaintiff" if current_user == plaintiff_name else "defendant")
    prompt = f"\n{plaintiff_name if current_user == plaintiff_name else defendant_name} has raised the following points: {user_input}. As a mediator, please suggest a fair resolution to {other_user}, addressing {current_user}'s concerns. You should also remind {current_user} of the potential costs they face if they go to court, including court costs (${costs['courtCostTotal']}) and opportunity cost (${costs['opportunityCost']})."

    # Corrected OpenAI API call for GPT-4
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": history},
            {"role": "user", "content": prompt}
        ]
    )

    ai_response = completion.choices[0].message['content']
    conversation_history.append({"author": "mediator", "message": f"AI Mediator to {other_user}: {ai_response}"})

    turn = 1 if turn == 2 else 2

    emit('ai_response', {'ai_response': ai_response, 'next_user': other_user, 'opportunityCost': costs['opportunityCost']}, to=current_user_sid)


@app.route('/')
def index():
    return "Mediation API with WebSocket is running."


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5002)