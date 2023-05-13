# GPT_TODO_Bot
Given a role, comes up with goals and subtasks for each goal. Plans for full user interaction including tracking goals, completing tasks, asking for help with tasks

# Installation
1. [Install Python 3](https://www.python.org/downloads/)
   a. Set it in your OS's PATH so you can access it by typing 'python' anywhere in the command line
2. Clone or download this repository (click the green Code Button/Dropdown for more information)
3. From this repository's directory, run pip install -r requirements.txt
4. Export your Open AI API key as an environment variable :arrow_down:
#### MacOS
```bash
OPENAI_API_KEY=YOUR-API-KEY-HERE
```
#### Windows Command Line
```shell
set OPENAI_API_KEY=YOUR-API-KEY-HERE
```
#### Windows Powershell
```powershell
$Env:OPENAI_API_KEY = 'YOUR-API-KEY-HERE'
```

# Run it from the repository's directory
`python bot.py`