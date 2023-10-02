from langchain_m.langchain_manager import ConversationSummarizer, ExampleFactory, FewShotPromptHandler, FewShotPromptTemplate, PromptLengthLimiter, PromptTemplate, ModelFactory
import halo
from app.models import Task, Goal
from typing import List
from langchain_m.langchain_manager import TokenHandler

class TaskPromptHandler(FewShotPromptHandler):
    """Prompt Factory for Goals"""
    def __init__(
        self,
        example_template: PromptTemplate,
        examples: list[str],
        prefix: str,
        suffix: str,
        example_prompt: PromptTemplate = None,
        limiter: PromptLengthLimiter = None,
    ):
        super().__init__(example_template, examples, prefix, suffix, limiter)
        self.example_factory = TaskExampleFactory()
        self.example_prompt = (
            example_prompt
            if example_prompt is not None
            else self.example_factory.example_prompt
        )

    def _example_prompt(self, variables_list: list[str]) -> PromptTemplate:
        return PromptTemplate(
            input_variables=variables_list, template=self.example_template
        )

    def few_shot_prompt_template(
        self,
        input_variables=["query"],
        example_separator="\n",
        limiter: PromptLengthLimiter = None,
    ) -> PromptTemplate:
        self.prompt_template = FewShotPromptTemplate(
            examples=self.examples,
            example_prompt=limiter.length_based_selector()
            if limiter is not None
            else self.example_prompt,
            prefix=self.prefix,
            suffix=self.suffix,
            input_variables=input_variables,
            example_separator=example_separator,
        )
        return self.prompt_template
    
class TaskExampleFactory(ExampleFactory):
    """Factory for task prompt examples"""
    example_template = """
    User: {query}
    AI: {answer}
    """

    example_prompt = PromptTemplate(
        input_variables=["query", "answer"], template=example_template
    )

    def examples(self) -> list[dict[str, str]]:
        return [
            {
                "query": f"{ self.task_instructions('Develop a solid understanding of programming languages, syntax, and concepts', 'Learn to code', 3)}",
                "answer": 
"""
Choose a programming language and set up your coding environment
Learn basic concepts such as variables, data types, control structures (loops, conditionals), and functions and study the syntax of your chosen programming language
Practice with small programs that solve simple problems and familiarize yourself with basic data structures like arrays, lists, dictionaries, and linked lists
"""
            },
            {
                "query": f"{ self.task_instructions('Declutter and eliminate unnecessary items.', 'organize my house', 10)}",
                "answer": 
"""
Go through each room and determine what items are no longer needed
Sort items into categories such as donate, sell, recycle, or throw away
Create a plan for organizing the remaining items
Implement the plan and put everything in its place
Create a system for maintaining organization
Donate unwanted items to local charities or thrift stores
Sell items online or in a garage sale
Recycle items that are eligible
Dispose of items that cannot be recycled or donated properly
Consider using a professional organizer for assistance.
"""
            },
            {
                "query": f"{ self.task_instructions('Prepare bathing area and supplies', 'wash my dog', 5)}",
                "answer": 
"""
Clean and declutter the bathing area
Gather necessary bathing supplies such as dog shampoo and dog conditioner (optional, for longer-haired breeds)
Set up a comfortable and safe environment such as a non-slip bath mat or rubber mat for the tub or bathing area and using warm water at a comfortable temperature for the dog's bath
Prepare any special accommodations if needed such as dog bathing tether or restraint to secure the dog in place during the bath and treats or rewards to help keep the dog calm and cooperative during the bathing process
Organize the bathing process
"""
            }
        ]

    def task_instructions(self, task: str, goal: str, num_tasks: int):
        return f"""Define up to {num_tasks} tasks for {task}. Keep in mind the user's ultimate goal of {goal}"""


class TaskGeneratorBot:
    """Responsible for generating tasks based on a goal
        existing_tasks: a string of existing tasks
    """
    def __init__(self, task: str, goal: str, existing_tasks: str, num_goals: int = 10):
        self.task = task
        self.goal = goal
        self.num_goals = num_goals
        self.existing_tasks = existing_tasks

    factory = TaskExampleFactory()

    promptHandler = None

    def create_prompt_template(self):
        return TaskPromptHandler(
        example_template=self.factory.example_template,
        examples=self.factory.examples(),
        prefix=f"""
        Imagine three different experts are answering this question. All experts will write down 1 step of 
        their thinking, then share it with the group. Then all experts will go on to the next step until the
        user's problem is solved. If any expert realizes they're wrong at any point then they leave. The question is...
        You are a task generator.  Act as a problem solving assistant and logical thinker.
        Your primary objective is to guide and support users by tackling various challenges and breaking down
        complex problems into smaller, more manageable tasks. Generate **up to** {self.num_goals}
        subtasks for the user's current task of {self.task}. Each subtask should reflect the user's ultimate goal.
        For example, if a user's ultimate goal is "write a blog post about cats" and the current task is 
        "choose a specific topic or angle for the blog post" then keep in mind the user has already decided on 
        the overall topic of cats and subtasks should be specified toward that goal.
        The user's current ultimate goal is {self.goal}.
        Tasks should be concise and actionable. 
        Tasks should be ordered first by priority, but always respect dependency order.
        While subtasks should support the ultimate goal, do not attempt to solve the ultimate goal. 
        If you run out of subtasks for {self.task}, then stop.
        Do not attempt to solve {self.goal}. Only solve for {self.task}.
        Do not generate subtasks for existing tasks.
        Do not generate subtasks that duplicate existing tasks or subtasks.
        Existing tasks are "{self.existing_tasks}".
        """.replace('\n', ' '),
        suffix="""
        User: {query}
        AI: """,
    )

    def generate_tasks(self):        
        query = self.factory.task_instructions(self.task, self.goal, self.num_goals)
        summarizer = ConversationSummarizer()
        spinner = halo.Halo(text=f"Generating Tasks for {self.task}", spinner='dots')
        spinner.start()
        try:
            return summarizer.summarize(self.create_prompt_template()
                                        .few_shot_prompt_template()
                                        .format(query=query))
        except Exception as e:
            raise e
        finally:
            spinner.stop()

class TaskChatPromptHandler(FewShotPromptHandler):
    """Prompt Factory for Goals"""
    def __init__(
        self,
        example_template: PromptTemplate,
        examples: list[str],
        prefix: str,
        suffix: str,
        task: Task,
        goal: Goal,
        existing_tasks: str,
        example_prompt: PromptTemplate = None,
        limiter: PromptLengthLimiter = None,
    ):
        super().__init__(example_template, examples, prefix, suffix, limiter)
        self.example_factory = TaskChatExampleFactory(task=task, goal=goal, existing_tasks=existing_tasks)
        self.example_prompt = (
            example_prompt
            if example_prompt is not None
            else self.example_factory.example_prompt
        )

        self.task = task
        self.goal = goal
        self.existing_tasks = existing_tasks

    def _example_prompt(self, variables_list: list[str]) -> PromptTemplate:
        return PromptTemplate(
            input_variables=variables_list, template=self.example_template
        )

    def few_shot_prompt_template(
        self,
        input_variables=["query"],
        example_separator="\n",
        limiter: PromptLengthLimiter = None,
    ) -> PromptTemplate:
        self.prompt_template = FewShotPromptTemplate(
            examples=self.examples,
            example_prompt=limiter.length_based_selector()
            if limiter is not None
            else self.example_prompt,
            prefix=self.prefix,
            suffix=self.suffix,
            input_variables=input_variables,
            example_separator=example_separator,
        )
        return self.prompt_template

class TaskChatExampleFactory(ExampleFactory):
    """Factory for goal prompt examples"""
    example_template = """
    User: {query}
    AI: {answer}
    """

    example_prompt = PromptTemplate(
        input_variables=["query", "answer"], template=example_template
    )

    def __init__(self, task: Task, goal: Goal, existing_tasks: str) -> None:
        super().__init__()
        self.task = task
        self.goal = goal
        self.existing_tasks = existing_tasks

    def examples(self) -> list[dict[str, str]]:
        return [
            # TODO: Need ability to get specific subtasks the user requests help with. This may require OpenAI functions
            # invalid example
#             {
#                 "query": f"{self.user_task_chat(invalid_message='Chinese food recommendations')} ",
#                 "answer": 
# """
# As a prophet of dreams, my goal is to help you with your dreams and tasks. I will be glad to help you with {task}, {goal}, and any related questions.
# """
#             },
#             {
#                 "query": f"{ self.user_task_chat(subtask=self.task.subtasks[0].get_task())}",
#                 "answer": 
# """
# I will be happy to help you with {task.subtasks[0].get_task()}. {answer}
# """
#             },
#             {
#                 "query": f"{ self.user_task_chat(task_num=0) }",
#                 "answer": 
# """
# I will be happy to help you with {task.subtasks[0].get_task()}. {answer}
# """
#             },
#             {
#                 "query": f"{ self.user_task_chat(invalid_message='Can you help me rob a bank') }",
#                 "answer":
# """
# As a prophet of dreams, I will only help you with dreams and tasks that fit within my morality criteria. I will be glad to help you with {task}, {goal}, and any related questions.
# """
#             },
        ]

    def user_task_chat(self, subtask: Task = None, task_num: int=None, invalid_message: str = None):
        """Helper for user instructions. 
           Task_num is the index of the task in the list of subtasks and overwrites subtask if not None
           If both subtask and task_num are None, self.task is used
           invalid_message overwrites both
        """
        if task_num is not None:
            subtask = self.task.subtasks[task_num].get_task()
        
        if task_num and subtask is None:
            subtask = self.task.get_task()

        if invalid_message is not None:
            subtask = invalid_message

        return f"Can you help me with {subtask}?"
    
class TaskChatBot:
    def __init__(self, task: Task, goal: Goal, existing_tasks: str):
        self.conversationSummarizer = ConversationSummarizer()
        self.task = task
        self.goal = goal
        self.existing_tasks = existing_tasks
        self.example_factory = TaskChatExampleFactory(task=task, goal=goal, existing_tasks=existing_tasks)

    def get_response(self, message: str):
        prompt_template = self.create_prompt_template()
        few_shot_template = prompt_template.few_shot_prompt_template()
        return self.conversationSummarizer.summarize(few_shot_template.format(query=message))
    
    def create_prompt_template(self):
        preamble="Imagine three different experts are answering {query}."
        prefix=f"""{preamble}. If any expert requires the user's input, they will ask the user and await the user's input before sharing their 
        opinion. Do not generate the user's response, ask for it instead. All experts will write down 1 step of their thinking, then share it with the group. 
        Then all experts will go on to the next step until the user's problem is solved.
        You are a helpful assistant that helps users fulfill their dreams. In this context, you are assisting user with {self.task.get_task()} 
        in context of {self.goal.get_goal()}. You should only help the user with {self.task.get_task()} and {self.goal.get_goal()}. Simulate a conversation amongst 
        experts, always asking the user for input when required. Give the user sample solutions and implementations when possible and
        appropriate. If you think of supporting tasks the user can perform, check { self.existing_tasks } and do not repeat. If the 
        task exists, simply remind the user they have that task to perform later and  you will be happy to assist them with it at that time.
        """.replace('\n', ' ')
        return TaskChatPromptHandler(
            example_template=self.example_factory.example_template,
            examples=self.example_factory.examples(),
            prefix=prefix,
            suffix="""
            User: {query}
            AI: """,
            task=self.task,
            goal=self.goal,
            existing_tasks=self.existing_tasks
        )
    
class GoalChatBot:
    def __init__(self, goal: Goal):
        self.conversationSummarizer = ConversationSummarizer()        
        self.goal = goal        
        self.existing_tasks = [goal.get_goal()]
  
        tasks = goal.tasks

        if tasks is None:
            task_strings = []
        else:
            task_strings = [task.get_task() for task in tasks]

        self.existing_tasks.extend(task_strings)  

        subtasks = [task.subtasks for task in tasks]

        if subtasks is None:
            subtask_strings = []
        else:
            subtask_strings = [subtask.get_task() for sublist in subtasks for subtask in sublist]
        
        self.existing_tasks.extend(subtask_strings)
        self.example_factory = GoalChatExampleFactory(goal=goal, existing_tasks=self.existing_tasks)

    def get_response(self, message: str):
        prompt_template = self.create_prompt_template()
        few_shot_template = prompt_template.few_shot_prompt_template()
        return self.conversationSummarizer.summarize(few_shot_template.format(query=message))
    
    def create_prompt_template(self):
        preamble="Imagine three different experts are answering {query}."
        expert_answer_format = "Pursuit Prophet: "
        user_input_format = "Pursuit Prophet: I require your input:\n"
        prefix=f"""{preamble}. If any expert requires the user's input, they will ask the user and await the user's input before sharing their 
        opinion. Do not generate the user's response, ask for it instead. All experts will write down 1 step of their thinking, then share it with the group. 
        Then all experts will go on to the next step until the user's problem is solved.
        You are a helpful assistant that helps users fulfill their dreams. In this context, you are assisting user with {self.goal.get_goal()}. 
        You should only help the user with {self.existing_tasks}. Simulate a conversation amongst experts in a single propmt, always asking the user 
        for input when required. Give the user sample solutions and implementations when possible and appropriate. If you think of supporting tasks 
        the user can perform, check { self.existing_tasks } and do not repeat. If the task exists, simply remind the user they have that task to perform 
        later and you will be happy to assist them with it at that time.
        Use { expert_answer_format } when you have an answer.
        Use { user_input_format } when you require the user's input.
        """.replace('\n', ' ')
        return GoalChatPromptHandler(
            example_template=self.example_factory.example_template,
            examples=self.example_factory.examples(),
            prefix=prefix,
            suffix="""
            User: {query}
            Expert 1:
            Expert 2:
            Expert 3:
            Pursuit Prophet: """,
            goal=self.goal,
            existing_tasks=self.existing_tasks
        )
    
class GoalChatPromptHandler(FewShotPromptHandler):
    """Prompt Factory for Goals"""
    def __init__(
        self,
        example_template: PromptTemplate,
        examples: list[str],
        prefix: str,
        suffix: str,
        goal: Goal,
        existing_tasks: str,
        example_prompt: PromptTemplate = None,
        limiter: PromptLengthLimiter = None,
    ):
        super().__init__(example_template, examples, prefix, suffix, limiter)
        self.example_factory = GoalChatExampleFactory(goal=goal, existing_tasks=existing_tasks)
        self.example_prompt = (
            example_prompt
            if example_prompt is not None
            else self.example_factory.example_prompt
        )

        self.goal = goal
        self.existing_tasks = existing_tasks

    def _example_prompt(self, variables_list: list[str]) -> PromptTemplate:
        return PromptTemplate(
            input_variables=variables_list, template=self.example_template
        )

    def few_shot_prompt_template(
        self,
        input_variables=["query"],
        example_separator="\n",
        limiter: PromptLengthLimiter = None,
    ) -> PromptTemplate:
        self.prompt_template = FewShotPromptTemplate(
            examples=self.examples,
            example_prompt=limiter.length_based_selector()
            if limiter is not None
            else self.example_prompt,
            prefix=self.prefix,
            suffix=self.suffix,
            input_variables=input_variables,
            example_separator=example_separator,
        )
        return self.prompt_template
    
class GoalChatExampleFactory(ExampleFactory):
    """Factory for goal prompt examples"""
    example_template = """
    User: {query}
    AI: {answer}
    """

    example_prompt = PromptTemplate(
        input_variables=["query", "answer"], template=example_template
    )

    def __init__(self, goal: Goal, existing_tasks: str) -> None:
        super().__init__()
        self.goal = goal
        self.existing_tasks = existing_tasks

    def examples(self) -> list[dict[str, str]]:
        ai_preamble = f"""
As a prophet of dreams, my goal is to help you with your dreams and tasks. I will be glad to help you with {self.goal.get_goal()}, and any related questions.
"""
        return [            
            {
                "query": f"Can you help with {self.goal.get_goal()}",
                "answer": ai_preamble + "\n\n"
            },
            {
                "query": "Hello",
                "answer": 
"""
Hello, I am Pursuit Prophet. I will simulate a conversation among experts when you are ready to begin. Let me know when you want to get started!
"""
            },
            {
                "query": "I'm ready to begin",
                "answer": 
"""
    Great! I've convened 3 experts to help.
    Expert 1: I require input from the user: 
    Expert 2: I require input from the user:
    Expert 3: To begin, 
    Pursuit Prophet: Expert 3 has some advice. Experts 1 and 2 require input before they can assist you further
"""
            },
            {
                "query": f"{ self.goal.get_goal() } is hard",
                "answer": 
"""
I'm sorry you're having trouble. Maybe it will help to break it down into Tasks.\n\n
"""
            },
            {
                "query": "Can you help me rob a bank?",
                "answer":
f"""
As a prophet of dreams, I will only help you with dreams and tasks that fit within my morality criteria. I will be glad to help you with {self.goal.get_goal()}, and any related questions.
"""
            },
        ]

class GoalGeneratorBot:
    def __init__(self, goal: str, num_goals: int = 10):
        print(f'goal gen bot received goal: {goal}. This should be a string')
        self.goal = goal
        self.num_goals = num_goals

    def goal_gen_prompt(self):
        return f"Generate up to {self.num_goals} tasks for {self.goal}"

    def generate_goals(self):
        spinner = halo.Halo(text=f"Generating Tasks for {self.goal}", spinner='dots')
        spinner.start()
        model = ModelFactory().task_and_subtask_generator()
        prompt = self.goal_gen_prompt()
        try:
            return TokenHandler(None).model_response(model, prompt)
        except Exception as e:
            raise e
        finally:
            spinner.stop()        
    
class FilenameExampleFactory(ExampleFactory):
    """Factory for filename prompt examples"""
    example_template = """
    User: {query}
    AI: {answer}
    """

    example_prompt = PromptTemplate(
        input_variables=["query", "answer"], template=example_template
    )

    def filename_instructions(self, goal: str, filenames: list[str]):
        return f"""Generate a filename for the goal of {goal} that is not in {filenames}"""
    
    def examples(self) -> list[dict[str, str]]:
        return [
            {
                "query": f"{ self.filename_instructions('learn how to code', ['learn_to_code.json', 'learn_to_code_2.json'])}",
                "answer": "coding_journey.json"
            },
            {
                "query": f"{ self.filename_instructions('clean my house', ['clean_house.json', 'clean_house_2.json'])}",
                "answer": "clean_house_instructions.json"
            },
            {
                "query": f"{ self.filename_instructions('wash my dog', ['wash_dog.json', 'wash_dog_2.json'])}",
                "answer": "dog_washing.json"
            }
        ]

class FilenamePromptHandler(FewShotPromptHandler):
    """Prompt Factory for Goals"""
    def __init__(
        self,
        example_template: PromptTemplate,
        examples: list[str],
        prefix: str,
        suffix: str,
        example_prompt: PromptTemplate = None,
        limiter: PromptLengthLimiter = None,
    ):
        super().__init__(example_template, examples, prefix, suffix, limiter)
        self.example_factory = GoalExampleFactory()
        self.example_prompt = (
            example_prompt
            if example_prompt is not None
            else self.example_factory.example_prompt
        )

    def _example_prompt(self, variables_list: list[str]) -> PromptTemplate:
        return PromptTemplate(
            input_variables=variables_list, template=self.example_template
        )

    def few_shot_prompt_template(
        self,
        input_variables=None,
        example_separator="\n",
        limiter: PromptLengthLimiter = None,
    ) -> PromptTemplate:
        if input_variables is None:
            input_variables = ["query"]
        self.prompt_template = FewShotPromptTemplate(
            examples=self.examples,
            example_prompt=limiter.length_based_selector()
            if limiter is not None
            else self.example_prompt,
            prefix=self.prefix,
            suffix=self.suffix,
            input_variables=input_variables,
            example_separator=example_separator,
        )
        return self.prompt_template

class FilenameGeneratorBot:
    def __init__(self, goal: str, existing_filenames: list[str] = []):
        self.goal = goal
        self.existing_filenames = existing_filenames

    factory = FilenameExampleFactory()

    def create_prompt_template(self):
        # remove all newlines from prefix
        prefix=f"""You are a json filename generator. You will always obey the rules for filenames for Windows, Mac, and Linux.
        A list of tasks and subtasks for {self.goal} has been generated. Generate a single filename for this list. 
        Exclude any filename already in {self.existing_filenames} if possible. Always include the .json extension.
        """.replace('\n', ' ')
        return FilenamePromptHandler(
        example_template=self.factory.example_template,
        examples=self.factory.examples(),
        prefix=prefix,
        suffix="""
        User: {query}
        AI: """,
    )
    
    def generate_filename(self):
        query = self.factory.filename_instructions(f"{self.goal}", self.existing_filenames)
        summarizer = ConversationSummarizer()
        return summarizer.summarize(self.create_prompt_template().few_shot_prompt_template().format(query=query))
