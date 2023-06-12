from langchain_m.langchain_manager import ConversationSummarizer, ExampleFactory, FewShotPromptHandler, FewShotPromptTemplate, PromptLengthLimiter, PromptTemplate
import halo
from app.app import Task

class GoalPromptHandler(FewShotPromptHandler):
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

class GoalExampleFactory(ExampleFactory):
    """Factory for goal prompt examples"""
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
                "query": f"{ self.goal_instructions('learn how to code', 3)}",
                "answer": 
"""
Develop a solid understanding of programming languages, syntax, and concepts.
Gain practical experience in writing code and solving programming problems.
Acquire the ability to design and develop software applications independently.
"""
            },
            {
                "query": f"{ self.goal_instructions('clean my house', 10)}",
                "answer": 
"""
Declutter and organize rooms.
Dust and clean surfaces.
Vacuum and mop floors.
Clean and sanitize kitchen and bathrooms.
Wash, fold, and put away laundry.
Clean windows, mirrors, and glass.
Tidy outdoor areas.
Organize closets, drawers, and cabinets.
Empty and clean trash bins.
Wipe down frequently touched surfaces.
"""
            },
            {
                "query": f"{ self.goal_instructions('wash my dog', 5)}",
                "answer": 
"""
Prepare bathing area and supplies.
Wet dog's fur with warm water.
Apply and lather dog shampoo.
Thoroughly rinse off shampoo.
Dry dog's fur with a towel.
"""
            }
        ]

    def goal_instructions(self, primary_goal: str, num_goals: int):
        return f"""Define up to {num_goals} goals that fulfill the primary goal of '{primary_goal}'"""

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
        While subtasks should support the ultimate goal, do not attempt to solve theultimate goal. 
        If you run out of subtasks for {self.task}, then stop.
        Do not attempt to solve {self.goal}. Only solve for {self.task}.
        Do not generate subtasks for existing tasks.
        Do not generate subtasks that duplicate existing tasks.
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
        finally:
            spinner.stop()

class TaskChatBotFactory(ExampleFactory):
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
            }]

class TaskChatBot:
    def __init__(self, task: Task):
        self.conversationSummarizer = ConversationSummarizer()
        self.task = task

    def get_response(self, message: str):
        return self.conversationSummarizer.summarize(message)


class GoalGeneratorBot:
    def __init__(self, goal: str, num_goals: int = 10):
        self.goal = goal
        self.num_goals = num_goals

    factory = GoalExampleFactory()

    def create_prompt_template(self):
        # remove all newlines from prefix
        prefix=f"""Answer the following query using the tree of thoughts method. Only after you reflect on all 
        of your thoughts, rate them and build upon the promising ones creating a new set of thoughts. Repeat 
        until a conclusive answer is found (i.e. do a breadth first search). You are a goal generator. 
        Act as a problem solving assistant and logical thinker. Your primary objective is to guide and support 
        users by tackling various challenges and breaking down complex problems into smaller, more manageable 
        tasks. Generate up to {self.num_goals} goals for the user's goal of {self.goal}. Goals should be concise 
        and acitonable. Goals should be ordered first by priority, but always respect dependency order. For instance, 
        if a user's goal is to bake a cake, it's very important to mix the batter, but first you must have the 
        necessary ingredients!
        """.replace('\n', ' ')
        return GoalPromptHandler(
        example_template=self.factory.example_template,
        examples=self.factory.examples(),
        prefix=prefix,
        suffix="""
        User: {query}
        AI: """,
    )

    def generate_goals(self):
        query = self.factory.goal_instructions(f"{self.goal}", self.num_goals)
        summarizer = ConversationSummarizer()
        return summarizer.summarize(self.create_prompt_template().few_shot_prompt_template().format(query=query))
    
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
