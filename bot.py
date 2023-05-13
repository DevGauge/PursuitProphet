"""
USE CASE
Title: Todo List ChatGPTBot

Actor: User (ex fitness enthusiast)

Description:
A user interacts with the ChatGPTBot to receive personalized coaching, set goals, create subtasks for achieving those goals, and track progress.

Preconditions:

The user has an OpenAI API token for authentication.
The user has a compatible device or browser to interact with the bot.

Postconditions:
The user receives personalized advice and support.
The user can track their progress through completed goals and subtasks.

Fitness Coach Use Case Example:
The user initializes the ChatGPTBot with their OpenAI API token.
The ChatGPTBot authenticates the user and welcomes them to the Personal Fitness Coach session.
The user defines their role as "Personal Fitness Coach."
The ChatGPTBot generates five fitness-related goals based on the user-defined role using the ChatGPT API.
The user reviews the goals and decides to keep them, modify them, or ask the bot to generate new goals.
The ChatGPTBot records the goals and their associated subtasks.
The user interacts with the bot using slash commands to create, complete, or update goals and subtasks.
/goal create: Creates a new goal.
/goal n complete: Marks goal n as complete.
/subtask create: Creates a new subtask for a goal.
/subtask n complete: Marks subtask n as complete.
The ChatGPTBot tracks message history, including sender information (user or system), and displays it in a scrolling format similar to chat.openai.com.
The ChatGPTBot provides contextually relevant advice and guidance on fitness-related topics based on the user's input and progress.
The user may ask the ChatGPTBot to generate additional goals at any time.
The user can set priorities for subtasks, and the ChatGPTBot will suggest tasks based on priority or order entered.
The ChatGPTBot confirms the completion of a goal or subtask by asking the user and interpreting their affirmative answers. In cases of ambiguous responses, the bot uses RNG to make a choice and confirms with the user before execution.
When the user ends the session, the ChatGPTBot reminds them that nothing shared is confidential, and the user controls all data.

Alternative Flows:

A. The user provides an invalid OpenAI API token.

The ChatGPTBot informs the user of the authentication error and asks them to provide a valid token.
B. The user requests to switch to another role (e.g., "Nutritionist").

The ChatGPTBot informs the user that it cannot handle multiple roles simultaneously and asks them to continue with the current role or restart the session with the new role.
Exceptions:

If the ChatGPTBot encounters an error or unexpected situation, it informs the user and provides guidance on how to proceed.

If the user exceeds the token limit for a request, the ChatGPTBot divides the request into smaller parts and sends them one by one within the token limit.
"""
# TO DO

# Implement message history tracking.
# Assist the user with a goal.
# Handle ambiguous or unclear affirmative responses regarding goal completion using RNG.
# Determine if there are additional responses required and ask ChatGPT to provide those responses for long-term goals.
# Determine tokens being sent when providing "training" data.
# Handle errors and unexpected situations and inform the user.
# Confirm with the user that the goal should be removed.
# Test the bot extensively to ensure all functionality works as expected.
# When user creates a goal, ask if they want to generate subtasks for it, then work on the goal/subtasks
# Work on subtasks in addition to goal

# Standard imports
import datetime
import json
import os
# 3rd party imports
from colorama import Fore, Style
import halo
import openai

class ChatBot:
    def __init__(self, api_key=None):
        self.io_manager = IOManager(role='')
        if api_key is None:
            api_key = self.io_manager.get_open_ai_key()
        self.gpt3_interface = GPT3Interface(io_manager=self.io_manager, openapi_key=api_key)
        self.goal_manager = GoalManager(io_manager=self.io_manager, gpt3_interface=self.gpt3_interface)
    
    def run(self):
        """Main function"""
        self.display_welcome_message()
        self.set_assistant_role()
        self.goal_manager.goals = self.gpt3_interface.suggest_goals()
        self.goal_manager.goals = self.goal_manager.strip_goals_and_save(self.goal_manager.goals)
        self.io_manager.ask_user_to_review_goals(self.goal_manager.goals)
        user_choice = self.io_manager.get_user_choice(['keep', 'modify', 'new'])
        if user_choice == 'modify' or user_choice == 'new':
            self.request_goals_from_user()
        for n in range(len(self.goal_manager.goals)):
            self.goal_manager.generate_subtasks(n)
        self.goal_manager.handle_user_task_interaction()
        self.goal_manager.save_goals_to_disk_in_json()

    def set_role(self, role):
        self.io_manager.role = role

    def display_welcome_message(self):
        """Display the welcome message"""        
        welcome_message = "Welcome to Devgauge's Todo List ChatGPTBot. What goal would you like help accomplishing?"
        self.io_manager.assistant_message(welcome_message)
        
    def request_goals_from_user(self):
        """Request goals from the user"""
        #send user message asking what goals would help fulfill the role
        message = f"You will now act as a goal generator for a user who wants to {self.io_manager.role}. Generate as many goals as possible up to 10. You will always only provide goals without preceding numbers. Goals should be separated by a new line."
        self.io_manager.system_message(message, to_user=False, to_gpt=True)
        user_response = input()
        self.io_manager.user_message(user_response)
        self.goal_manager.strip_goals_and_save(user_response)

    def set_assistant_role(self):
        """Set the assistant role based on user input"""
        self.set_role(self.io_manager.get_user_input("Please enter the role for the assistant: "))
        self.io_manager.system_message(f"For the remainder of the conversation, I want you to act and respond as a master planner for a user who wants to {self.io_manager.role}", to_user=False, to_gpt=True)
        self.gpt3_interface.send_message_to_gpt(self.io_manager.messages)

class GoalManager:
    def __init__(self, io_manager, gpt3_interface):
        self.io_manager = io_manager
        self.gpt3_interface = gpt3_interface
        self.goals = {}
        self.completed_goals = []

    def create_file_json(self):
        return {
            "role": self.io_manager.role,
            "goals": self.goals,
            "completed_goals": self.completed_goals,
        }

    def handle_slash_command(self, text):
        """Handle slash commands"""
        commands = {
            "/goal": ['create', 'complete']
            #"/subtask": ['create', 'complete'],
        }
        
        # if text includes a valid command
        if text.split(" ")[0] in commands:
            command, action = text.split(" ")[:2]
            if command == "/goal":
                if action == "create":
                    goal = text.split(" ", 2)[2]
                    self.goals[goal] = []
                    self.io_manager.system_message(f"Created new goal: {goal}", to_user=True, to_gpt=True)
                    return True
                elif action == "complete":
                    goal_number = int(text.split(" ")[2])
                    self.mark_goal_as_complete(goal_number)
                    return True
            else:
                self.io_manager.system_message(f"Invalid command. Valid commands are {json.dumps(commands, indent=4)}")
                return False
        return False

    def confirm_completion(self, item):
        """Ask the user to confirm whether a goal or subtask is complete."""
        self.io_manager.assistant_message(f"Have you completed {item}? Please respond with 'yes' or 'no'.")
        user_input = self.io_manager.get_user_choice(["yes", "no", "y", "n"])
        if user_input == 'yes':
            # Mark the item as complete and remove it from the list
            self.io_manager.assistant_message(f"Great job! {item} has been marked as complete.")
        else:
            self.io_manager.assistant_message(f"Okay, we'll keep working on {item}.")

    def generate_subtasks(self, n):
        """Assist the user with a goal"""
        task = list(self.goals.keys())[n]
        sys_message = f"You will now generate tasks. You will attempt to simplify {task} with the overall goal of meeting {self.io_manager.role} Do you suggest breaking {task} into substasks? If yes, please respond with a list of subtasks separated by new lines. Do not respond with an affirmation or context. Provide only an unformatted list with no leading or trailing characters including numbers or hyphens or any markdown. If no, please suggest how the user can start working on the goal."
        self.io_manager.system_message(sys_message, to_user=False, to_gpt=True)
        response = self.gpt3_interface.send_message_to_gpt(self.io_manager.messages)
        text = response['choices'][0]['message']['content']
        subtasks = text.split('\n')  # Split the response into subtasks
        self.goals[task] = subtasks  # Assign the subtasks to the corresponding goal
        self.io_manager.assistant_message(text)
    
    def ask_if_user_wants_to_work_on_task(self, task):
        """Ask the user if they want to work on a task."""
        message = f"Do you want to work on {task}?"
        self.io_manager.assistant_message(message)
        user_input = self.io_manager.get_user_choice(["yes", "no", "y", "n"])
        if user_input == 'yes':
            return True
        return False

    def handle_user_task_interaction(self):
        """Iterate through the user's tasks, asking if they want to work on it, breaking it down if needed, and providing assistance."""
        for goal, tasks in self.goals.items():
            print(f"Goal: {goal}")
            for task in tasks:
                # Ask the user if they want to work on the subtask
                user_wants_to_work_on_subtask = self.ask_if_user_wants_to_work_on_task(task)
                if not user_wants_to_work_on_subtask:
                    continue

                # Provide assistance with the subtask
                self.gpt3_interface.provide_assistance_with_task(task)

    def mark_goal_as_complete(self, n):
        """Mark the nth goal as complete."""
        goal = list(self.goals.keys())[n]
        self.completed_goals.append({goal: self.goals[goal]})
        del self.goals[goal]
        self.io_manager.system_message(f"Goal {n+1} '{goal}' marked as complete.")

    def strip_goals_and_save(self, goals):
        """Strip the goals from the response and save them"""
        #strip the goals from the response
        goals = goals.split("\n")
        # if goal starts with number or number and period, strip it
        goals = [goal.split(" ", 1)[1] if goal != "" and goal[0].isdigit() else goal for goal in goals]
        # if goal starts with period, strip it
        goals = [goal[1:] if goal != "" and goal[0] == "." else goal for goal in goals]
        # strip leading and trailing whitespace
        goals = [goal.strip() for goal in goals]
        self.goals = {goal: [] for goal in goals}  # Store each goal as a key with an empty list as its value
        return self.goals

    def save_goals_to_disk_in_json(self):
        """Save the goals to disk in JSON format."""
        sys_message = "Saving goals to disk."
        self.io_manager.system_message(sys_message, to_user=True, to_gpt=False)
        # eclude existing files
        excluded_filenames = [filename for filename in os.listdir() if filename.endswith(".json")]

        sys_filename_message = f"Please give me a filename to save {self.io_manager.role} using the \".json\" extension. Take care to obey the rules of macOS, Windows, and Unix-based operating systems. Exclude the following filenames from the final result: {excluded_filenames}"
        self.io_manager.system_message(sys_filename_message, to_user=False, to_gpt=True)
        response = self.gpt3_interface.send_message_to_gpt(self.io_manager.messages, loading_text="Generating...")
        filename = response['choices'][0]['message']['content']

        if os.path.exists(filename):
            # append timestamp to filename
            sys_filename_message = sys_filename_message + str(datetime.datetime.now())
        
        json_dict = {
            "role": self.io_manager.role,
            "goals": self.goals,
            "completed_goals": self.completed_goals,
        }        
        json_object = json.dumps(json_dict, indent=4)

        with open(self.strip_invalid_file_chars(filename), "w", encoding="utf-8") as f:
            f.write(json_object)
        
        sys_save_complete_message = f"Saved session to disk as {filename}."
        self.io_manager.system_message(sys_save_complete_message, to_user=True, to_gpt=False)

    def strip_invalid_file_chars(self, filename):
        """Strip invalid characters from a filename."""
        invalid_chars = ["/", "\\", ":", "*", "?", "\"", "<", ">", "|"]
        for char in invalid_chars:
            filename = filename.replace(char, "")
        return filename

class GPT3Interface:
    def __init__(self, io_manager, openapi_key, model="gpt-3.5-turbo"):        
        self.io_manager = io_manager
        self.gpt = model
        openai.api_key = openapi_key

    def send_message_to_gpt(self, messages, loading_text='Thinking'):
        """Send a list of messages to the ChatGPT API"""
        spinner = halo.Halo(text=loading_text, spinner='dots')
        spinner.start()
        try:
            return openai.ChatCompletion.create(
                model=self.gpt,
                messages=messages
            )
        finally:
            spinner.stop()

    def suggest_goals(self, num_goals=10):
        """Define the objective"""
        message = f"Define as many goals as possible up to {num_goals} goals that fulfill the role of {self.io_manager.role}. Please provide only a list separated by new lines with no additional context."
        #send message to ChatGPT
        self.io_manager.append_message("system", message)
        response = self.send_message_to_gpt(self.io_manager.messages)
        text = response['choices'][0]['message']['content']
        return text

    def provide_assistance_with_task(self, task):
        """Ask the user what subtask they want to work on and provide assistance."""
        # Ask the user what task they want to work on
        # If the bot can provide assistance with the task, do so
        # Otherwise, let the user know that the bot can't provide the specific assistance requested but can provide other types of assistance
        message = f"Acting with the goal of {self.io_manager.role}, what assistance can you provide with {task}? Keep your answer concise and to the point, providing practical advice whenever possible. If unable to complete a task, let the user know and ask if they'd like to move on to the next task or want you to wait for them, using \"/goal complete\" to mark the task as complete."
        self.io_manager.system_message(message, to_user=False, to_gpt=True)
        response = self.send_message_to_gpt(self.io_manager.messages)
        text = response['choices'][0]['message']['content']
        self.io_manager.assistant_message(text)

class IOManager:
    color_map = {
        "user": Fore.GREEN,
        "assistant": Fore.BLUE,
        "system": Fore.RED,
    }

    def __init__(self, role):
        self.role = role
        self.messages = []

    def formatted_text_output(self, message_type, text):
        """Format the text output based on the type of message"""
        color = self.color_map[message_type]
        print(f"{color}{text}{Style.RESET_ALL}\n")

    def append_message(self, role, message):
        """Append a message to the message list"""
        self.messages.append({"role": role, "content": message})

    def assistant_message(self, message, to_user=True):
        """Send a message from the assistant to the user"""
        if to_user:
            self.formatted_text_output("assistant", message)
        self.append_message("assistant", message)

    def system_message(self, message, to_user=True, to_gpt=False):
        """Send a message from the system to the user"""
        if to_user:
            self.formatted_text_output("system", message)
        if to_gpt:
            self.append_message("system", message)

    def user_message(self, message):
        """Record a message from the user"""
        self.append_message("user", message)

    def get_user_input(self, prompt):
        """Get input from the user and append it to the messages list"""
        user_response = input(prompt)
        # if self.handle_slash_command(user_response) is False:
        #     self.messages.append({"role": "user", "content": user_response})
        return user_response

    def get_user_choice(self, choices):
        """Get user input and ensure it's one of the provided choices."""
        while True:
            user_input = input().strip().lower()  # Get user input, remove leading/trailing whitespace and convert to lowercase
            self.user_message(user_input)
            if user_input in choices:
                # if user input begins with y, return True
                if user_input.startswith("y"):
                    user_input = 'yes'
                    return True
                user_input = 'no'
                return user_input
            else:
                self.assistant_message("Invalid choice. Please choose from the following options: " + ", ".join(choices))

    def ask_user_to_review_goals(self, goals):
        """Ask the user to review the goals"""
        #send user message asking them to review the goals
        formatted_goals = "\n".join([f"{i+1}. {goal}" for i, goal in enumerate(goals)])
        message = f"I've generated the following goals for you: \n\n{formatted_goals}\n\nWould you like to keep (keep) them, modify (modify) them, ask me to generate new goals (new), or provide your own goals? (list goals, separated by a new line)"
        self.assistant_message(message)

    def get_open_ai_key(self):
        """Get the OpenAI API key from the environment or crash"""
        key = os.getenv("OPENAI_API_KEY")
        if key is not None:
            return key

        to_user_message="Please set your OpenAI API key in the environment variables using the key OPENAI_API_KEY"
        sys_message="OPENAI_API_KEY not found in environment variables"
        self.system_message(to_user_message)
        raise UnboundLocalError(sys_message)

def main(argv):
    """Main function"""
    # check if user provided an OpenAI API key with the -k flag
    if len(argv) > 1 and argv[1] == "-k":
        api_key = argv[2]
        bot = ChatBot(api_key=api_key)
    else:
        bot = ChatBot()
    bot.run()

if __name__ == "__main__":
    import sys
    # pass commandline arguments to main function
    main(sys.argv[1:])
