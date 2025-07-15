# AI Crew for Instagram Post

## Example Response :
- Cursor.com
- Just want you to get me the stuff very quickly. Everything within 1 minute. I just want too much stuff

```
[DEBUG]: [Chief Creative Director] Task output: **Option 1: (Speed & Efficiency)** A high-speed photograph capturing hands in motion over a keyboard, illuminated by multiple monitors displaying code. A vibrant cityscape at sunset fills the background, symbolizing the limitless possibilities and rapid pace of coding with Cursor. The image is crisp, 4k, and a wide shot emphasizing the energy and efficiency of the platform.

**Option 2: (Natural Language Coding)** A close-up, 4k shot of a person's face, softly lit by a screen. A subtle smile conveys understanding and ease. The reflection in their eyes shows abstract shapes transforming into clean, structured code, representing the effortless translation of thought into code with Cursor. The lighting is soft and professional.

**Option 3: (Community & Support)** A 4k, crisp image of a diverse group collaborating around a table, their faces lit by the warm glow of laptops. Lively discussion and a supportive atmosphere are palpable. Futuristic technology subtly integrated into the background hints at Cursor's AI-powered revolution, fostering a sense of community and shared purpose.




########################
## Here is the result
########################

Your post copy:
Here are 3 Instagram ad copy options for Cursor.com:

**Option 1 (Focus on Speed & Efficiency):**

> Stop coding, start creating! 🚀 Cursor lets you write code at the speed of thought with AI. Generate code from natural language, debug in a flash, and say goodbye to repetitive tasks. ⚡️ Download Cursor for FREE and unlock your coding potential! #AICoding #CodeFaster #Cursor

**Option 2 (Focus on Natural Language Coding):**

> Imagine coding with the power of AI. ✨ Cursor is your AI coding partner, turning your natural language into clean, efficient code. Effortless coding, powerful results. Try Cursor Pro FREE for 14 days! Link in bio. #NaturalLanguageCoding #AI #DeveloperTools #CodingLife

**Option 3 (Focus on Community & Support):**

> Level up your coding game with Cursor! Join a community of developers who are building the future with AI. Get instant support, share your creations, and code at the speed of thought. Download Cursor for FREE and join the revolution! #CodingCommunity #AIRevolution #Cursor #Developer
```

Your midjourney description:
**Option 1: (Speed & Efficiency)** A high-speed photograph capturing hands in motion over a keyboard, illuminated by multiple monitors displaying code. A vibrant cityscape at sunset fills the background, symbolizing the limitless possibilities and rapid pace of coding with Cursor. The image is crisp, 4k, and a wide shot emphasizing the energy and efficiency of the platform.

**Option 2: (Natural Language Coding)** A close-up, 4k shot of a person's face, softly lit by a screen. A subtle smile conveys understanding and ease. The reflection in their eyes shows abstract shapes transforming into clean, structured code, representing the effortless translation of thought into code with Cursor. The lighting is soft and professional.

**Option 3: (Community & Support)** A 4k, crisp image of a diverse group collaborating around a table, their faces lit by the warm glow of laptops. Lively discussion and a supportive atmosphere are palpable. Futuristic technology subtly integrated into the background hints at Cursor's AI-powered revolution, fostering a sense of community and shared purpose.

## Introduction
This project is an example using the CrewAI framework to automate the process of coming up with an instagram post. CrewAI orchestrates autonomous AI agents, enabling them to collaborate and execute complex tasks efficiently.

#### Instagram Post
[![Instagram Post](https://img.youtube.com/vi/lcD0nT8IVTg/0.jpg)](https://www.youtube.com/watch?v=lcD0nT8IVTg "Instagram Post")

By [@joaomdmoura](https://x.com/joaomdmoura)

- [CrewAI Framework](#crewai-framework)
- [Running the script](#running-the-script)
- [Details & Explanation](#details--explanation)
- [Using Local Models with Ollama](#using-local-models-with-ollama)
- [License](#license)

## CrewAI Framework
CrewAI is designed to facilitate the collaboration of role-playing AI agents. In this example, these agents work together to generate a creative and trendy instagram post.

## Running the Script
This example uses OpenHermes 2.5 through Ollama by default so you should to download [Ollama](ollama.ai) and [OpenHermes](https://ollama.ai/library/openhermes).

You can change the model by changing the `MODEL` env var in the `.env` file.

- **Configure Environment**: Copy ``.env.example` and set up the environment variables for [Browseless](https://www.browserless.io/), [Serper](https://serper.dev/).
- **Install Dependencies**: Run `poetry install --no-root`.
- **Execute the Script**: Run `python main.py` and input your idea.

## Details & Explanation
- **Running the Script**: Execute `python main.py`` and input your idea when prompted. The script will leverage the CrewAI framework to process the idea and generate an instagram post.
- **Key Components**:
  - `./main.py`: Main script file.
  - `./tasks.py`: Main file with the tasks prompts.
  - `./agents.py`: Main file with the agents creation.
  - `./tools/`: Contains tool classes used by the agents.

## Using Local Models with Ollama
This example run entirely local models, the CrewAI framework supports integration with both closed and local models, by using tools such as Ollama, for enhanced flexibility and customization. This allows you to utilize your own models, which can be particularly useful for specialized tasks or data privacy concerns.

### Setting Up Ollama
- **Install Ollama**: Ensure that Ollama is properly installed in your environment. Follow the installation guide provided by Ollama for detailed instructions.
- **Configure Ollama**: Set up Ollama to work with your local model. You will probably need to [tweak the model using a Modelfile](https://github.com/jmorganca/ollama/blob/main/docs/modelfile.md), I'd recommend playing with `top_p` and `temperature`.

## License
This project is released under the MIT License.


