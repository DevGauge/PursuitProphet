from langchain import PromptTemplate, FewShotPromptTemplate, LLMChain
from langchain.prompts.example_selector import LengthBasedExampleSelector
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory
from langchain.callbacks import get_openai_callback
from abc import ABC, abstractmethod, abstractproperty, abstractstaticmethod

parameters_list = ["query", "answer"]

class TokenHandler:
    """Handles token reporting"""

    def __init__(self, llm_chain: LLMChain):
        self.llm_chain = llm_chain

    def handle(self, message: str):
        with get_openai_callback() as cb:
            result = self.llm_chain.run(message)
            print(result)
            print(f"Spent a total of {cb.total_tokens} tokens")
        return result


class ConversationSummarizer:
    def __init__(self):
        summarization_model = ModelFactory().summarizer()
        self.conversation = ConversationChain(
            llm=summarization_model,
            memory=ConversationSummaryBufferMemory(
                llm=summarization_model, max_token_limit=1000
            ),
        )

    def summarize(self, prompt):
        counter = TokenHandler(self.conversation)
        return counter.handle(prompt)


class ModelFactory:
    """Creates models with preset parameters for various tasks"""

    # region Expensive Models
    _gpt_3_5_turbo = "gpt-3.5-turbo"

    # region private methods
    def _creative_gpt3(self):
        return ChatOpenAI(model_name=self._gpt_3_5_turbo, temperature=0.8)

    def _strict_gpt3(self):
        return ChatOpenAI(model_name=self._gpt_3_5_turbo, temperature=0.2)

    # endregion

    def summarizer(self):
        """Returns a creative model for high-value summarization. May be more expensive than `cheap_summarizer()`, should be more accurate."""
        return self._creative_gpt3()
    
    def chatbot(self):
        return self._creative_gpt3()

    def instructor(self):
        """Returns a strict model for providing user-instructions. User instructions on utilizing the app's features should probably be hard-coded.
        That said, this may be useful for providing instructions for a user-defined goal for example, but not for chatting about the goal since
        it will likely start to repeat itself fairly quickly.
        """
        return self._strict_gpt3()

    # endregion

    # region Cheap Models
    _davinci_003 = "davinci-003"

    def _creative_davinci(self):
        return ChatOpenAI(model_name=self._davinci_003, temperature=0.8)

    def _strict_davinci(self):
        return ChatOpenAI(model_name=self._davinci_003, temperature=0.2)

    def cheap_summarizer(self):
        """Returns a low-cost creative model for summarization. May be less accurate and provide less value to the llm than `summarizer()`"""
        return self._creative_davinci()

    def cheap_instructor(self):
        """Returns a low-cost strict model for instruction. May be less accurate and provide less value to the user than `instructor()`"""
        return self._strict_davinci()

    # endregion


class PromptLengthLimiter(ABC):
    def __init__(self, max_words: int, examples: list, example_prompt: PromptTemplate):
        self.max_words = max_words
        self.examples = examples
        self.example_prompt = example_prompt

    def length_based_selector(self):
        return LengthBasedExampleSelector(
            self.examples, self.example_prompt, self.max_words
        )


class FewShotPromptHandler(ABC):
    def __init__(
        self,
        example_template: PromptTemplate,
        examples: list[str],
        prefix: str,
        suffix: str,
        limiter: PromptLengthLimiter = None,
    ):
        self.example_template = example_template
        self.examples = examples
        self.prefix = prefix
        self.suffix = suffix
        self.prompt_template = None
        self.limiter = limiter

    @abstractmethod
    def _example_prompt(self, variables_list: list[str]) -> PromptTemplate:
        return PromptTemplate(
            input_variables=variables_list, template=self.example_template
        )

    @abstractmethod
    def few_shot_prompt_template(
        self,
        prompt: str,
        input_variables=["query"],
        variables_list: list[str] = ["query", "answer"],
        example_separator="\n",
        limiter: PromptLengthLimiter = None,
    ) -> PromptTemplate:
        self.prompt_template = FewShotPromptTemplate(
            examples=self.examples,
            example_prompt=limiter.length_based_selector()
            if limiter is not None
            else self._example_prompt(variables_list),
            prefix=self.prefix,
            suffix=self.suffix,
            input_variables=input_variables,
            example_separator=example_separator,
        )
        return self.prompt_template
    

class ExampleFactory(ABC):
    @abstractproperty
    def example_template(self) -> str:
        """The example template to use with few shot templates"""
        return self._example_template

    @example_template.setter
    def example_template(self, value):
        self._example_template = value

    @example_template.deleter
    def example_template(self):
        del self._example_template

    @abstractproperty
    def example_prompt(self) -> PromptTemplate:
        """The example prompt to use with few shot templates"""
        return self._example_prompt

    @example_prompt.setter
    def example_prompt(self, value):
        self._example_prompt = value

    @example_prompt.deleter
    def example_prompt(self):
        del self._example_prompt

    @abstractmethod
    def examples(self) -> list[dict[str, str]]:
        """interaction examples between user and LLM"""




#region implementation
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

    def _example_prompt(self, variables_list=["query", "answer"]) -> PromptTemplate:
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

class GoalExampleFactory(ExampleFactory):
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
                "query": f"{ self._goal_instructions('learn how to code', 3)}",
                "answer": """Develop a solid understanding of programming languages, syntax, and concepts.
                Gain practical experience in writing code and solving programming problems.
                Acquire the ability to design and develop software applications independently."""
            },
            {
                "query": f"{ self._goal_instructions('clean my house', 10)}",
                "answer": """Declutter and organize rooms.
                Dust and clean surfaces.
                Vacuum and mop floors.
                Clean and sanitize kitchen and bathrooms.
                Wash, fold, and put away laundry.
                Clean windows, mirrors, and glass.
                Tidy outdoor areas.
                Organize closets, drawers, and cabinets.
                Empty and clean trash bins.
                Wipe down frequently touched surfaces."""
            },
            {
                "query": f"{ self._goal_instructions('wash my dog', 5)}",
                "answer": """Prepare bathing area and supplies.
                Wet dog's fur with warm water.
                Apply and lather dog shampoo.
                Thoroughly rinse off shampoo.
                Dry dog's fur with a towel.
                """
            }
        ]

    def _goal_instructions(self, role: str, num_goals: int):
        return f"""Define up to {num_goals} goals that fulfill the role of {role}"""


factory = GoalExampleFactory()

promptHandler = GoalPromptHandler(
    example_template=factory.example_template,
    examples=factory.examples(),
    prefix="You are a goal generator. Generate up to n goals for the user's prompt",
    suffix="""
    User: {query}
    AI: """,
)
goal = "buy a car"
query = factory._goal_instructions(f"{goal}", 3)

summarizer = ConversationSummarizer()
summarizer.summarize(promptHandler.few_shot_prompt_template().format(query=query))
summarizer.summarize(promptHandler.few_shot_prompt_template().format(query=f"Great, thanks. Can you help me work on {goal} now?"))
while True:
    prompt = input()
    summarizer.summarize(promptHandler.few_shot_prompt_template().format(query=prompt))
#endregion implementation