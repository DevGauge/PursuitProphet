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

import os
import json
import openai
from colorama import Fore, Style
import halo


class Bot:
    """Create a bot using GPT-3.5 to act as an assistant, helping the user complete a to-do list"""
    role = None
    messages = []
    completed_goals = []

    color_map = {
        "user": Fore.GREEN,
        "assistant": Fore.BLUE,
        "system": Fore.RED,
    }

    def __init__(self, model="gpt-3.5-turbo"):
        self.gpt = model
        self.goals = {}  # Initialize goals as an empty dictionary
        self.initialize()

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
                    self.system_message(f"Created new goal: {goal}", to_user=True, to_gpt=True)
                    return True
                elif action == "complete":
                    goal_number = int(text.split(" ")[2])
                    self.mark_goal_as_complete(goal_number)
                    return True
            else:
                self.system_message(f"Invalid command. Valid commands are {json.dumps(commands, indent=4)}")
                return False

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
        if self.handle_slash_command(user_response) is False:
            self.messages.append({"role": "user", "content": user_response})
        return user_response

    def get_open_ai_key(self):
        """Get the OpenAI API key from the environment or crash"""
        key = os.getenv("OPENAI_API_KEY")
        if key is not None:
            return key

        to_user_message="Please set your OpenAI API key in the environment variables using the key OPENAI_API_KEY"
        sys_message="OPENAI_API_KEY not found in environment variables"
        self.system_message(to_user_message)
        raise UnboundLocalError(sys_message)
    
    def initialize(self):
        """Instantiate Gpt-3.5"""
        self.system_message("Use this bot at your own risk. Nothing shared is confidential, but no data is tied to you personally. ")
        openai.api_key = self.get_open_ai_key()

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

    def display_welcome_message(self):
        """Display the welcome message"""        
        welcome_message = "Welcome to the Todo List ChatGPTBot. What goal would you like help accomplishing?"
        self.assistant_message(welcome_message)        

    def set_assistant_role(self):
        """Set the assistant role based on user input"""
        self.role = self.get_user_input("Please enter the role for the assistant: ")
        self.messages.append({"role": "system", "content": f"For the remainder of the conversation, I want you to act and respond as {self.role}"})
        self.send_message_to_gpt(self.messages)
    
    def suggest_goals(self, num_goals=10):
        """Define the objective"""
        message = f"Define as many goals as possible up to {num_goals} goals that fulfill the role of {self.role}. I want you to first generate 10 goals, then ask yourself what rank the goals should be in, ranked by importance toward fulfilling the role. Return goals in a numbered list. Exclude any commentary, only providing the numbered list. I will provide instructions to the  user and additional text will interfere with this process."
        #send message to ChatGPT
        self.append_message("system", message)
        response = self.send_message_to_gpt(self.messages)
        text = response['choices'][0]['message']['content']
        return text
    
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

    def ask_user_to_review_goals(self, goals):
        """Ask the user to review the goals"""
        #send user message asking them to review the goals
        formatted_goals = "\n".join([f"{i+1}. {goal}" for i, goal in enumerate(goals)])
        message = f"I've generated the following goals for you: \n\n{formatted_goals}\n\nWould you like to keep (keep) them, modify (modify) them, ask me to generate new goals (new), or provide your own goals? (list goals, separated by a new line)"
        self.assistant_message(message)

    def get_user_choice(self, choices):
        """Get user input and ensure it's one of the provided choices."""
        while True:
            user_input = input().strip().lower()  # Get user input, remove leading/trailing whitespace and convert to lowercase
            self.user_message(user_input)
            if user_input in choices:
                return user_input
            else:
                self.assistant_message("Invalid choice. Please choose from the following options: " + ", ".join(choices))

    def confirm_completion(self, item):
        """Ask the user to confirm whether a goal or subtask is complete."""
        self.assistant_message(f"Have you completed {item}? Please respond with 'yes' or 'no'.")
        user_input = self.get_user_choice(["yes", "no"])
        if user_input == 'yes':
            # Mark the item as complete and remove it from the list
            self.assistant_message(f"Great job! {item} has been marked as complete.")
        else:
            self.assistant_message(f"Okay, we'll keep working on {item}.")

    def request_goals_from_user(self):
        """Request goals from the user"""
        #send user message asking what goals would help fulfill the role
        message = f"What goals would help fulfill the role of {self.role}? Please provide 5 goals, separated by a new line"
        self.assistant_message(message)
        user_response = input()
        self.user_message(user_response)

    def generate_subtasks(self, n):
        """Assist the user with a goal"""
        task = list(self.goals.keys())[n]
        sys_message = f"Given your role as {self.role}, do you suggest breaking {task} into substasks? If yes, please respond with \"I think it's a good idea to break {task} into subtasks.\": numbered list of subtasks separated by new lines. If no, please suggest how the user can start working on the goal. Do not provide any additional context, instrucitons, advice, etc. I will provide it to the user."
        self.append_message("system", sys_message)
        response = openai.ChatCompletion.create(
            model=self.gpt,
            messages=self.messages
        )
        text = response['choices'][0]['message']['content']
        subtasks = text.split('\n')  # Split the response into subtasks
        self.goals[task] = subtasks  # Assign the subtasks to the corresponding goal
        self.assistant_message(text)

    def handle_user_task_interaction(self):
        """Iterate through the user's tasks, asking if they want to work on it, breaking it down if needed, and providing assistance."""
        for task in self.goals:
            # Ask the user if they want to work on the task
            user_wants_to_work_on_task = self.ask_if_user_wants_to_work_on_task(task)
            if not user_wants_to_work_on_task:
                continue

            # Ask user what subtask they want to work on and provide assistance
            self.provide_assistance_with_task(task)

    def ask_if_user_wants_to_work_on_task(self, task):
        """Ask the user if they want to work on a task."""
        message = f"Do you want to work on {task}?"
        self.assistant_message(message)
        user_input = self.get_user_choice(["yes", "no"])
        if user_input == 'yes':
            return True
        return False

    def provide_assistance_with_task(self, task):
        """Ask the user what subtask they want to work on and provide assistance."""
        # Ask the user what task they want to work on
        # If the bot can provide assistance with the task, do so
        # Otherwise, let the user know that the bot can't provide the specific assistance requested but can provide other types of assistance
        message = f"Acting with the goal of {self.role}, what assistance can you provide with {task}? Keep your answer concise and to the point, providing practical advice whenever possible. If unable to complete a task, let the user know and ask if they'd like to move on to the next task or want you to wait for them, using \"/goal complete\" to mark the task as complete."
        self.system_message(message, to_user=False, to_gpt=True)
        response = self.send_message_to_gpt(self.messages)
        text = response['choices'][0]['message']['content']
        self.assistant_message(text)

    def mark_task_as_complete(self, task):
        """Mark a task as complete."""
        self.goals.remove(task)
        self.completed_goals.append(task)

    def save_goals_to_disk_in_json(self):
        """Save the goals to disk in JSON format."""
        sys_message = "Saving goals to disk."
        self.system_message(sys_message, to_user=True, to_gpt=False)

        sys_filename_message = f"Please give me a filename to save {self.role} using the \".json\" extension. Take care to obey the rules of macOS, Windows, and Unix-based operating systems."
        self.system_message(sys_filename_message, to_user=False, to_gpt=True)
        response = self.send_message_to_gpt(self.messages, loading_text="Generating...")
        filename = response['choices'][0]['message']['content']
        
        json_dict = {
            "role": self.role,
            "goals": self.goals,
            "completed_goals": self.completed_goals,
        }        
        json_object = json.dumps(json_dict, indent=4)

        with open(filename, "w") as f:
            f.write(json_object)
        
        sys_save_complete_message = f"Saved session to disk as {filename}."
        self.system_message(sys_save_complete_message, to_user=True, to_gpt=False)        

    def run(self):
        """Main function"""
        self.display_welcome_message()
        self.set_assistant_role()
        goals = self.suggest_goals()
        goals = self.strip_goals_and_save(goals)
        self.ask_user_to_review_goals(goals)
        user_choice = self.get_user_choice(['keep', 'modify', 'new'])
        if user_choice == 'modify' or user_choice == 'new':
            self.request_goals_from_user()
        for n in range(len(self.goals)):
            self.assist_user_with_goal(n)
        bot.save_goals_to_disk_in_json()

if __name__ == "__main__":
    bot = Bot()
    bot.run()
