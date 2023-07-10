from abc import ABC, abstractmethod, abstractproperty, abstractstaticmethod

from langchain import PromptTemplate, FewShotPromptTemplate, LLMChain
from langchain.prompts.example_selector import LengthBasedExampleSelector
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory
from langchain.callbacks import get_openai_callback

parameters_list = ["query", "answer"]

class TokenHandler:
    """Handles token reporting"""

    def __init__(self, llm_chain: LLMChain):
        self.llm_chain = llm_chain

    def handle(self, message: str):
        try:
            with get_openai_callback() as cb:
                result = self.llm_chain.run(message)
                print("memory: ", self.llm_chain.memory)
                print("chat result: ", result)
                print(f"Spent a total of {cb.total_tokens} tokens")
                return result
        except Exception as e:
            raise e

class ConversationSummarizer:
    def __init__(self, memory: ConversationSummaryBufferMemory = None):
        summarization_model = ModelFactory().summarizer()
        if memory is None:
            memory = ConversationSummaryBufferMemory(
                llm=summarization_model, max_token_limit=4000
            )
        self.conversation = ConversationChain(
            llm=summarization_model,
            memory=memory
        )

    def summarize(self, prompt):
        counter = TokenHandler(self.conversation)
        
        return counter.handle(prompt)


class ModelFactory:
    """Creates models with preset parameters for various tasks"""

    # region Expensive Models
    _gpt_3_5_turbo = "gpt-3.5-turbo"
    _gpt_3_5_turbo_16k = "gpt-3.5-turbo-16k"
    _gpt_4 = "gpt-4"

    # region private methods
    def _creative_gpt3(self):
        return ChatOpenAI(model_name=self._gpt_3_5_turbo, temperature=0.8)
    
    def _creative_gpt4(self):
        return ChatOpenAI(model_name=self._gpt_4, temperature=0.8)
    
    def _creative_gpt3_16k(self):
        return ChatOpenAI(model_name=self._gpt_3_5_turbo_16k, temperature=0.8)

    def _strict_gpt3(self):
        return ChatOpenAI(model_name=self._gpt_3_5_turbo, temperature=0.2)

    # endregion

    def summarizer(self):
        """Returns a creative model for high-value summarization. May be more expensive than `cheap_summarizer()`, should be more accurate."""
        return self._creative_gpt4()
    
    def chatbot(self):
        return self._creative_gpt4()
    
    def filename_bot(self):
        return ChatOpenAI(model_name=self._gpt_3_5_turbo, temperature=1.0) # max variation to prevent duplication of filenames

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