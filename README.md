# BMO Chatbot for Obsidian

Generate and brainstorm ideas while creating your notes using Large Language Models (LLMs) from Ollama, LM Studio, Anthropic, OpenAI, Mistral AI, and more for Obsidian.

<p align="center">
  <img src="README_images/original-example.png" alt="original_example">
  <img src="README_images/dataview-example.png" alt="dataview_example">
  <img src="README_images/eli5-example.png" alt="eli5_example">
</p>

## Features

-   **Interact with self-hosted Large Language Models (LLMs):** Use the REST API URLs provided to interact with self-hosted Large Language Models (LLMs) using [Ollama](https://ollama.ai) or [LM Studio](https://lmstudio.ai/).
-   **Profiles:** Create chatbots with specific knowledge, personalities, and presets.
-   **Chat from anywhere in Obsidian:** Chat with your bot from anywhere within Obsidian.
-   **Chat with current note:** Use your chatbot to reference and engage within your current note.
-   **Chatbot renders in Obsidian Markdown:** Receive formatted responses in Obsidian Markdown for consistency.
-   **Customizable bot name:** Personalize the chatbot's name.
-   **Prompt Select Generate:** Prompt, select, and generate within your editor.
-   **Save current chat history as markdown:** Use the `/save` command in chat to save current conversation.

## Requirements

If you want to interact with self-hosted Large Language Models (LLMs) using [Ollama](https://ollama.ai) or [LM Studio](https://lmstudio.ai/), you will need to have the self-hosted API set up and running. You can follow the instructions provided by the self-hosted API provider to get it up and running. Once you have the REST API URL for your self-hosted API, you can use it with this plugin to interact with your models.

Access to other models may require an API key.

Please see [instructions](https://github.com/longy2k/obsidian-bmo-chatbot/wiki) to setup with other LLMs providers.

Explore some models at [GPT4ALL](https://gpt4all.io/index.html) under the "Model Explorer" section or [Ollama's Library](https://ollama.ai/library).

## How to activate the plugin

Install method:

To activate the plugin from this repo:

1. Navigate to the plugin's folder in your terminal.

```
cd /path/to/your/obsidian-vault/.obsidian/plugins
```

2. Clone the repository.

```
git clone https://github.com/NoguchiShigeki/MyBMO
```

3. Run `npm install` to install any necessary dependencies for the plugin.

```
cd MyBMO
npm install
```

4. Once the dependencies have been installed, run `npm run build` or `npm run dev` to build the plugin.

```
npm run build
```

```
npm run dev
```

5. Once the plugin has been built, it should be ready to activate.
   Enable: 'Settings' > 'Community plugins' > 'Installed plugins' > 'MyBMO' > 'Enable'.

## Getting Started

To start using the plugin, enable it in your settings menu and insert an API key or REST API URL from a provider. After completing these steps, you can access the bot panel by clicking on the bot icon in the left sidebar.

## Commands

-   `/help` - Show help commands.
-   `/model` - List or change model.
    -   `/model 1` or `/model "llama2"`
        -   ...
-   `/profile` - List or change profiles.
    -   `/profile 1` or `/profile [PROFILE-NAME]`
-   `/prompt` - List or change prompts.
    -   `/prompt 1` or `/prompt [PROMPT-NAME]`
-   `/maxtokens [VALUE]` - Set max tokens.
-   `/temp [VALUE]` - Change temperature range from 0 to 1.
-   `/ref on | off` - Turn on or off reference current note.
-   `/append` - Append current chat history to current active note.
-   `/save` - Save current chat history to a note.
-   `/clear` or `/c` - Clear chat history.
-   `/stop` or `/s` - Stop fetching response.

## Supported Models

-   Any self-hosted models using [Ollama](https://ollama.ai).
    -   See [instructions](https://github.com/longy2k/obsidian-bmo-chatbot/wiki) to setup Ollama with Obsidian.
-   Any self-hosted models using OpenAI's REST API URL endpoints.
    -   [LM Studio](https://lmstudio.ai/)
    -   [LocalAI](https://github.com/mudler/LocalAI)
-   Anthropic
    -   claude-instant-1.2
    -   claude-2.0
    -   claude-2.1
    -   claude-3-haiku-20240307
    -   claude-3-sonnet-20240229
    -   claude-3-opus-20240229
-   Mistral AI's models
-   Google Gemini Pro
-   OpenAI
    -   gpt-3.5-turbo
    -   gpt-3.5-turbo-1106
    -   gpt-4
    -   gpt-4-turbo-preview
    -   These following models are added in this folk:
    -   gpt-4-turbo
    -   gpt-4-turbo-2024-04-09
    -   gpt-4o
    -   gpt-4o-2024-05-13
-   Any Openrouter provided models.

## Other Notes

"BMO" is a tag name for this project. Inspired by the character "BMO" from Adventure Time.

Be MOre!

## Contributing

Any ideas or support is highly appreciated :)

If you have any bugs, improvements, or questions please create an issue or discussion!

## Big thanks to Longy2k and the original project! 🎉

This link is for Longy2k, he deserves more than a coffee!

<a href='https://ko-fi.com/K3K8PNYT8' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi1.png?v=3' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
