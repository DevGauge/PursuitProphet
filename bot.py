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

"""
TO DO

Implement message history tracking.
Assist the user with a goal.
Handle ambiguous or unclear affirmative responses regarding goal completion using RNG.
Determine if there are additional responses required and ask ChatGPT to provide those responses for long-term goals.
Determine tokens being sent when providing "training" data.
Handle errors and unexpected situations and inform the user.
Confirm with the user that the goal should be removed.
Implement user input handling.
Write the main function to run the bot.
Test the bot extensively to ensure all functionality works as expected.
"""

import os
import openai
from colorama import Fore, Style

class Bot:
    """Create a bot using GPT-3.5 to act as an assistant, helping the user complete a to-do list"""
    gpt = None
    role = None
    messages = []
    goals = []
    
    color_map = {
        "user": Fore.GREEN,
        "assistant": Fore.BLUE,
        "system": Fore.RED,
    }

    user_color = color_map["user"]
    assistant_color = color_map["assistant"]
    system_color = color_map["system"]

    def formatted_text_output(self, message_type, text):
        """Format the text output based on the type of message"""
        color = self.color_map[message_type]
        print(f"{color}{text}{Style.RESET_ALL}\n")

    def assistant_message(self, message, to_user=True):
        """Send a message from the assistant to the user"""
        if to_user:
            self.formatted_text_output("assistant", message)
        self.messages.append({"role": "assistant", "content": message})

    def system_message(self, message):
        """Send a message from the system to the user"""
        self.formatted_text_output("system", message)

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
        self.system_message("Initializing Custom Bot")
        openai.api_key = self.get_open_ai_key()
        self.gpt = "gpt-3.5-turbo"
    
    def welcome(self):
        """Define the role"""
        self.assistant_message("Welcome to the Todo List ChatGPTBot. What role would you like me to fill today?")
        self.role = input()
        self.messages.append({"role": "system", "content": f"for the remainder of the conversation, I want you to act and respond as {self.role}"})
        openai.ChatCompletion.create(
            model=self.gpt,
            messages=self.messages
        )

    def suggest_goals(self):
        """Define the objective"""
        message = f"Define 5 goals that fulfill the role of {self.role}. Return goals in a numbered list. Do not provide additional context or output as I will provide it to the user."
        #send message to ChatGPT
        self.messages.append({"role": "system", "content": message})
        response = openai.ChatCompletion.create(
            model=self.gpt,
            messages=self.messages
        )
        text = response['choices'][0]['message']['content']
        return text
    
    def strip_goals_and_save(self, goals):
        """Strip the goals from the response and save them"""
        #strip the goals from the response
        goals = goals.split("\n")
        # if goal starts with number or number and period, strip it
        goals = [goal.split(" ", 1)[1] if goal[0].isdigit() else goal for goal in goals]
        # if goal starts with period, strip it
        goals = [goal[1:] if goal[0] == "." else goal for goal in goals]
        # strip leading and trailing whitespace
        goals = [goal.strip() for goal in goals]
        self.goals = goals
        return goals

    def ask_user_to_review_goals(self, goals):
        """Ask the user to review the goals"""
        #send user message asking them to review the goals
        message = f"I've generated the following goals for you: \n\n{goals}\n\nWould you like to keep (keep) them, modify (modify) them, ask me to generate new goals (new), or provide your own goals? (list 5 goals, separated by a new line)"
        self.messages.append({"role": "assistant", "content": message})
        self.formatted_text_output("assistant", message)
        user_response = input()
        self.messages.append({"role": "user", "content": user_response})

    def request_goals_from_user(self):
        """Request goals from the user"""
        #send user message asking what goals would help fulfill the role
        message = f"What goals would help fulfill the role of {self.role}? Please provide 5 goals, separated by a new line"
        self.formatted_text_output("assistant", message)
        user_response = input()
        self.messages.append({"role": "user", "content": user_response})

    def assist_user_with_goal(self, n):
        """Assist the user with a goal"""        
        sys_message = f"Given your role as {self.role}, do you suggest breaking this task into substasks? If yes, please respond with \"I think it's a good idea to break this task into subtasks.\": numbered list of subtasks separated by new lines. If no, please suggest how the user can start working on the goal. Do not provide any additional context, instrucitons, advice, etc. I will provide it to the user."
        self.messages.append({"role": "system", "content": sys_message})
        response = openai.ChatCompletion.create(
            model=self.gpt,
            messages=self.messages
        )
        text = response['choices'][0]['message']['content']
        self.formatted_text_output("assistant", text)

    def handle_user_input(self):
        user_response = input()
        self.messages.append({"role": "user", "content": user_response})

def main():
    """Main function"""
    bot = Bot()
    bot.initialize()
    bot.welcome()
    goals = bot.suggest_goals()
    bot.ask_user_to_review_goals(goals)
    bot.request_goals_from_user()

if __name__ == "__main__":
    main()
