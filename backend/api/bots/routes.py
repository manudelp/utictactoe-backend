import numpy as np
import api.utils as utils  # This import should now work correctly
import time
from colorama import Style, Fore
from typing import List, Tuple, Dict, Any, Union, Optional
from flask import jsonify, request
from . import bot_routes, AGENTS
import logging

logger = logging.getLogger(__name__)

@bot_routes.route('/get-bot-list', methods=['GET', 'OPTIONS'])
def get_bot_list():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        bot_list = []
        for agent_id, agent in AGENTS.items():
            bot_info = {
                'id': agent.id,
                'name': agent.name,
                'icon': agent.icon,
                'description': agent.description,
                'difficulty': agent.difficulty
            }
            bot_list.append(bot_info)
        
        return jsonify(bot_list), 200
    except Exception as e:
        logger.error(f"Error getting bot list: {e}")
        return jsonify({'error': 'Failed to get bot list'}), 500
    

@bot_routes.route('/get-bot-move', methods=['POST', 'OPTIONS'])
def get_bot_move():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Get the JSON data from the request
        data = request.json
        
        # Print the JSON data for debugging
        # print("\n\nJSON data received:", data)

        # Extract 'board' and 'activeMiniBoard' from the JSON data
        id = data.get('bot') 
        bot = AGENTS.get(id)
        
        if bot is None:
            print(f"Invalid bot id: {id}")  # Print error message for debugging
            return jsonify({'error': 'Invalid bot id'}), 400  # Return error response
        
        board = data.get('board')
        active_mini_board = data.get('activeMiniBoard')
        turn = data.get('turn')

        # Check if 'board' is present in the JSON data
        if board is None:
            print("Invalid input - missing board")  # Print error message for debugging
            return jsonify({'error': 'Invalid input, missing Board'}), 400  # Return error response

        # Convert the board to a 3x3x3x3 4D NumPy array
        board_array = np.array(board, dtype=int).reshape((3, 3, 3, 3))
        board_results = utils.get_board_results(board_array)
        if active_mini_board is not None:
            board_to_play = board_array[active_mini_board[0]][active_mini_board[1]]
        else:
            board_to_play = None

        # # # DEBUG BEFORE MOVE (UNCOMMENT ME)
        # print(f"It will be turn {turn} for the bot, meaning turn for {agent_turn}")
        # print(f"Their received board to play in is {active_mini_board}, which looks like this currently:\n{board_to_play}")  # Print the turn for debugging
        # print("Their received board is:")  # Print the turn for debugging
        # utils.fancyBoardPrinter(board_array)  # Print the board for debugging
        # print(f"\nReceived board results is \n{board_results}\n")  # Print the board results for debugging

        # Check if the game is already over
        winner = utils.get_winner(board_results)
        if winner != 0:
            print("che alguien gano pa'")
            return jsonify({'error': 'Game Over'}), 400
        
        # Get the move from the agent
        if turn == "X":
            board_array = board_array * -1
            move = bot.action(board_array, active_mini_board)
        else:
            move = bot.action(board_array, active_mini_board)

        # # # DEBUG AFTER MOVE (UNCOMMENT ME)
        # board_copy = board_array.copy()
        # board_copy[move[0]][move[1]][move[2]][move[3]] = 1 if turn == "O" else -1
        # board_copy_results = utils.get_board_results(board_copy)
        # print("\nBoard after move:")  # Print the board after the move for debugging
        # utils.fancyBoardPrinter(board_copy)  # Print the board for debugging
        # print(f"Current active Mini Board or Board to Play is {active_mini_board}")  # Print the active mini board for debugging
        # print(f"\nNow board results is \n{board_copy_results}!!\n")  # Print the board results for debugging

        # Convert the move to a tuple of integers
        move_response = (int(move[0]), int(move[1]), int(move[2]), int(move[3]))
        print(f"\nMove calculated by {bot.name}:", move_response)  # Print the calculated move for debugging

        # Return the move and agent's id as a JSON response
        return jsonify({'move': move_response, 'bot_name': bot.name})
    except Exception as e:
        print(f"\nError: {e}\n")

        # Return an internal server error response
        return jsonify({'error': 'Internal Server Error'}), 500

@bot_routes.route('/agents-reset', methods=['POST', 'OPTIONS'])
def agents_reset():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Identify the agent to reset
        id = request.json.get('id')
        bot = AGENTS.get(id)
    except:
        print(Fore.RED + Style.BRIGHT + "Error: No se pudo identificar el agente a resetear" + Style.RESET_ALL)
        return jsonify({'error': 'No se pudo identificar el agente a resetear'}), 400
        
    try:
        # Reset the agents
        bot.reset()
        # Return a success response
        return jsonify({'message': 'Agent reset successfully'})
    except Exception as e:
        print(f"\nError: {e}\n")

        # Return an internal server error response
        return jsonify({'error': 'Internal Server Error, el agente no se reseteo (routes.py, agents_reset)'}), 500

# Initialize Agent Load
@bot_routes.route('/agent-load', methods=['POST', 'OPTIONS'])
def agent_load():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Identify the agent to load
        data = request.get_json()
        bot_id = data.get('id')
        bot = AGENTS.get(bot_id)
        
        if bot is None:
            return jsonify({'error': 'Bot not found'}), 404
        
        # Load/Reset the agents
        bot.reset()  # Using reset since load method might not exist

        # Print the agent name for debugging
        print(Fore.GREEN + Style.BRIGHT + f"\n{bot.name} loaded successfully\n" + Style.RESET_ALL)

        # Return a success response
        return jsonify({'message': bot.name + ' loaded successfully'})
    except Exception as e:
        print(Fore.RED + Style.BRIGHT + f"\nCATASTROPHIC FAILURE: {e}\n" + Style.RESET_ALL)
        return jsonify({'error': 'Failed to load bot'}), 500
