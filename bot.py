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

Fitness Coach Goal Example:
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

# Assist the user with a goal.
# Handle ambiguous or unclear affirmative responses regarding goal completion using RNG.
# Determine if there are additional responses required and ask ChatGPT to provide those responses for long-term goals.
# Confirm with the user that the goal should be removed.
# Test the bot extensively to ensure all functionality works as expected.
# When user creates a goal, ask if they want to generate subtasks for it, then work on the goal/subtasks
# Allow user to create goal
# Allow user to edit goal
# Work on subtasks in addition to goal

# Standard imports
import datetime
import json
import os
import sys
import uuid
import threading
# 3rd party imports
from colorama import Fore, Style
from termcolor import colored
from dotenv import load_dotenv
import halo
import openai
# Local imports
sys.path.insert(0, './langchain')
from langchain_m.langchain_module import TaskGeneratorBot, GoalGeneratorBot, FilenameGeneratorBot
from app.models import Goal, Task, User, db
from app.app import app_instance
from sqlalchemy.exc import SQLAlchemyError
from flask import session


load_dotenv()
class SingletonMeta(type):
    """Singleton metaclass. If instance already exists, it will be returned. Otherwise, a new instance will be created."""
    _instances = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class ChatBot:
    def __init__(self, api_key=None):
        self.io_manager = IOManager()
        if api_key is None:
            api_key = self.io_manager.get_open_ai_key()
        self.goal_manager = GoalManager(io_manager=self.io_manager)
        self.goal_gen_bot = GoalGeneratorBot(goal='', num_goals=10)
    
    def run(self):
        """Main function"""
        print()
        self.display_welcome_message()
        self.set_assistant_primary_goal()
        print(dir(self.goal_gen_bot))
        self.goal_gen_bot.goal = self.io_manager.primary_goal.get_goal()
        suggested_goals = self.goal_gen_bot.generate_goals()        
        self.goal_manager.goals = self.goal_manager.strip_goals_and_save(suggested_goals)
        self.io_manager.ask_user_to_review_goals(self.goal_manager.goals)
        user_choice = self.io_manager.get_user_choice(['keep', 'modify', 'new'])
        if user_choice == 'modify' or user_choice == 'new':
            pass #TODO: implement modify and new using langchain
        for n in range(len(self.goal_manager.goals)):
            self.goal_manager.generate_subtasks(n)
            # self.goal_manager.handle_user_task_interaction()
        self.goal_manager.save_goals_to_disk_in_json()

    def set_primary_goal(self, user_input, user = None):
        if user:
            primary_goal = Goal(user_input, user)
        else:
            print('creating temp user')
            temp_user = User(email=str(uuid.uuid4()) + "@temp.com",  # Use a dummy email for the temporary user
                                       password=generate_password_hash("temp_password"),  # Use a dummy password for the temporary user
                                       is_temporary=True)
            db.session.add(temp_user)
            db.session.commit()
            primary_goal = Goal(user_input, user_id=temp_user.id)
            
        try:
            db.session.add(primary_goal)
            db.session.commit()
            session['temp_user_id'] = temp_user.id
            return primary_goal.id

        except SQLAlchemyError as e:
            db.session.rollback()
            raise e

    def display_welcome_message(self):
        """Display the welcome message"""        
        welcome_message = "Hi! I'm Pursuit Prophet, brought to you by DevGauge."
        self.io_manager.assistant_message(welcome_message)

    def set_assistant_primary_goal(self, primary_goal=None):
        """Set the assistant role based on user input"""
        if primary_goal is None:
            self.set_primary_goal(self.io_manager.get_user_input("What are you dreaming of today?"))
        else:
            goal_id = self.set_primary_goal(primary_goal)
            return goal_id
        # print(f'{self.io_manager.primary_goal.goal} was set')
        
    
    def generate_goals(self, primary_goal, num_goals=10):
        """Generate goals using the OpenAI API"""
        
        print(f'generating goals for {primary_goal.get_goal()}')
        bot = GoalGeneratorBot(goal=primary_goal.get_goal(), num_goals=num_goals)
        #strip and save
        try:
            self.goal_manager.strip_tasks_and_save(bot.generate_goals(), primary_goal.id)
        except Exception as e:
            # go to error route
            raise e

    def generate_subtasks(self, task: Task, num_tasks=10):
        """Generate subtasks for a given goal"""
        return self.goal_manager.generate_subtasks(task, num_tasks)

class GoalManager:

    def __init__(self, io_manager):
        self.io_manager = io_manager
        self.completed_goals = []

    def create_file_json(self):
        return {
            "role": self.io_manager.primary_goal.get_goal(),
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
                    goal_text = text.split(" ", 2)[2]
                    goal = Goal(goal_text)
                    db.session.add(goal)
                    db.session.commit()
                    self.io_manager.user_instruction(f"Created new goal: {goal.goal}")
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

    def generate_subtasks(self, task: Task, num_subtasks=10):
        """Assist the user with a goal"""
        print(f'GoalManager generating subtasks for task {task.get_task()}')
        goal = Goal.query.filter_by(id=task.goal_id).first()
        existing_tasks = Task.query.filter_by(goal_id=goal.id).all()
        # convert existing tasks into a string separated by newlines
        existing_tasks = ", ".join([task.get_task() for task in existing_tasks])
        bot = TaskGeneratorBot(task=task.get_task(), goal=goal.get_goal(), existing_tasks=existing_tasks, num_goals=num_subtasks)
        response_text = bot.generate_tasks()
        text = self.sanitize_bot_goal_response(response_text)
        
        subtasks = text.split('\n')  # Split the response into subtasks
        # create a task object for each subtask
        subtasks = [Task(subtask, task.goal_id, parent_id=task.id) for subtask in subtasks]
        errors = [] # TODO handle errors thrown while saving subtasks
        for subtask in subtasks:
            try:
                db.session.add(subtask)
                db.session.commit()
            except SQLAlchemyError as err:
                db.session.rollback()
                app_instance.logger.log_event('ERR_add_subtask', {'Error encountered while saving': subtask.get_task(), 'Error': err, 'traceback': err.with_traceback()})
                errors.append(err)
                
            app_instance.logger.log_event('add_subtask', {'subtask': subtask})
        return subtasks
    
    def  ask_if_user_wants_to_work_on_task(self):
        """Ask the user if they want to work on a task."""
        message = "Do you want to work on this right now? Please respond with 'yes' or 'no'"
        self.io_manager.user_instruction(message)
        user_input = self.io_manager.get_user_choice(["yes", "no", "y", "n"])
        if user_input == 'yes':
            return True
        return False
    
    def sanitize_bot_goal_response(self, response_text):
        """Sanitize the bot's response to a goal."""
        
        if not isinstance(response_text, str):
            raise ValueError("Input should be a string.")
        
        # If there's no text, there's nothing to sanitize.
        if response_text == "":
            return response_text
        
        # If the response contains 2 newlines, split it into text and goals.
        # GPT likes to provide pretext, content, and posttext.
        # We're interested in the content and posttext.
        if "\n\n" in response_text:
            print("Response Text: " + response_text)
            text = response_text.split("\n\n")
            if len(text) > 2:
                goals = text[2:]
                print("Goals: " + str(goals))
            elif len(text) > 1:
                goals = text[:1]
            else:
                goals = text
            if len(text) > 3:
                commentary = text[3]
                print("Commentary: " + commentary)
            
            sanitized_goals = []
            for goal in goals:
                # If goal starts with a number or a number followed by a period, strip it
                if goal and goal[0].isdigit():
                    goal = goal.split(" ", 1)[1] if len(goal.split(" ", 1)) > 1 else ''
                
                # If goal starts with a period, strip it
                if goal and goal[0] == "." or goal and goal[0] == "-":
                    goal = goal[1:]
                
                # Strip leading and trailing whitespace
                if goal != "":
                    goal.strip()
                    sanitized_goals.append(goal)
            
            # Join the sanitized goals with "\n\n" and return the resulting string
            return "\n\n".join(sanitized_goals)

        # If none of the above conditions are met, return the original string.
        return response_text

    def handle_user_task_interaction(self):
        """Iterate through the user's tasks, asking if they want to work on it, breaking it down if needed, and providing assistance."""
        for goal, tasks in self.goals.items():
            for task in tasks:
                print(f"Goal: {goal}")
                print(f"Task: {task}")
                # Ask the user if they want to work on the subtask
                user_wants_to_work_on_subtask = self.ask_if_user_wants_to_work_on_task()
                if not user_wants_to_work_on_subtask:
                    continue
                # TODO Provide assistance with the subtask                

    def mark_goal_as_complete(self, n):
        """Mark the nth goal as complete."""
        goal = list(self.goals.keys())[n]
        del self.goals[goal]
        self.io_manager.system_message(f"Goal {n+1} '{goal}' marked as complete.")

    def strip_tasks_and_save(self, tasks, goal_id):        
        """Strip the goals from the response and save them"""
        #strip the goals from the response
        tasks = tasks.split("\n")
        # if goal starts with number or number and period, strip it
        tasks = [task.split(" ", 1)[1] if task != "" and task[0].isdigit() else task for task in tasks]
        # if goal starts with period, strip it
        tasks = [task[1:] if task != "" and task[0] == "." else task for task in tasks]
        # strip leading and trailing whitespace
        tasks = [task.strip() for task in tasks]
        tasks = [Task(task, goal_id) for task in tasks]
        print(f'goals: {[task.goal_id for task in tasks]}')
        errors = [] #TODO handle errors thrown while generating tasks
        for goal in tasks:
            try:
                db.session.add(goal)
                db.session.commit()
            except SQLAlchemyError as err:
                db.session.rollback()
                app_instance.logger.log_event('ERR_add_goal', {'Error encountered while saving': goal.get_task(), 'Error': err, 'traceback': err.with_traceback()})
                errors.append(err)

    def save_goals_to_disk_in_json(self):
        """Save the goals to disk in JSON format."""
        sys_message = "Saving goals to disk."
        self.io_manager.system_message(sys_message)
        # eclude existing files
        excluded_filenames = [filename for filename in os.listdir() if filename.endswith(".json")]

        filename_bot = FilenameGeneratorBot(goal=self.io_manager.primary_goal.get_goal(), existing_filenames=excluded_filenames)
        filename = filename_bot.generate_filename()

        if os.path.exists(filename):
            # append timestamp to filename
            sys_filename_message = sys_filename_message + str(datetime.datetime.now())
        
        json_dict = {
            "primary_goal": self.io_manager.primary_goal.get_goal(),
            "goals": self.goals,
            "completed_goals": self.completed_goals,
        }
        json_object = json.dumps(json_dict, indent=4)

        with open(self.strip_invalid_file_chars(filename), "w", encoding="utf-8") as f:
            f.write(json_object)
        
        sys_save_complete_message = f"Saved session to disk as {filename}."
        self.io_manager.system_message(sys_save_complete_message)

    def strip_invalid_file_chars(self, filename):
        """Strip invalid characters from a filename."""
        invalid_chars = ["/", "\\", ":", "*", "?", "\"", "<", ">", "|"]
        for char in invalid_chars:
            filename = filename.replace(char, "")
        return filename

class IOManager(metaclass=SingletonMeta):
    color_map = {
        "user": Fore.GREEN,
        "assistant": Fore.BLUE,
        "system": Fore.RED,
        "input": "green"
    }

    primary_goal: Goal = None

    def __init__(self, primary_goal: Goal = None):
        self.primary_goal = primary_goal

    def formatted_text_output(self, message_type, text):
        """Format the text output based on the type of message"""
        color = self.color_map[message_type]
        print(f"{color}{text}{Style.RESET_ALL}\n")

    def assistant_message(self, message):
        """Send a message from the assistant to the user"""
        self.formatted_text_output("assistant", message)

    def user_instruction(self, message):
        """Send a message from the assistant to the user"""
        self.formatted_text_output("user", message)

    def system_message(self, message):
        """Send a message from the system to the user"""        
        self.formatted_text_output("system", message)

    def get_user_input(self, prompt):
        """Get input from the user and append it to the messages list"""        
        user_response = input(colored(prompt + ' ', self.color_map["input"]))
        return user_response

    def get_user_choice(self, choices):
        """Get user input and ensure it's one of the provided choices."""
        while True:
            string_choices = ','.join(choices)
            user_input = self.get_user_input(f'[{string_choices}]: ').strip().lower()  # Get user input, remove leading/trailing whitespace and convert to lowercase
            if user_input in choices:
                # if user input begins with y, return True
                if user_input.startswith("y"):
                    user_input = 'yes'
                    return True
                user_input = 'no'
                return user_input
            else:
                self.user_instruction("Invalid choice. Please choose from the following options: " + ", ".join(choices))

    def ask_user_to_review_goals(self, goals):
        """Ask the user to review the goals"""
        #send user message asking them to review the goals
        formatted_goals = "\n".join([f"{i+1}. {goal}" for i, goal in enumerate(goals)])
        goal_message = f"I've generated the following goals for you: \n\n{formatted_goals}"
        self.assistant_message(goal_message)
        self.user_instruction("Would you like to keep them (keep), modify them (modify), or ask me to generate new goals (new)?")

    def get_open_ai_key(self):
        """Get the OpenAI API key from the environment or crash"""
        key = os.getenv("OPENAI_API_KEY")
        if key is not None:
            return key

        to_user_message="Please set your OpenAI API key in the environment variables using the key OPENAI_API_KEY"
        sys_message="OPENAI_API_KEY not found in environment variables"
        self.system_message(sys_message)
        self.user_instruction(to_user_message)
        sys.exit(1)

def main(argv):
    """Main function"""
    # check if user provided an OpenAI API key with the -k flag
    if len(argv) > 1 and argv[1] == "-k":
        api_key = argv[2]
        bot = ChatBot(api_key=api_key)
    else:
        # will exit if not set
        api_key = IOManager(None).get_open_ai_key()
        if api_key is not None:
            bot = ChatBot(api_key=api_key)
    bot.run()

if __name__ == "__main__":    
    # pass commandline arguments to main function
    main(sys.argv[1:])
    