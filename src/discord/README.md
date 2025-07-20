# Mixed Model Marriage

Small-scale Discord bots that blend OpenAI and Gemini models. Chat history is
chunked and embedded for local memory. If a chunk exceeds the configured token
limit it is summarized before storage using Gemini 1.5 Flash. The summarizer
model and token limit can be adjusted in `config.py` via `SUMMARIZER_MODEL_NAME`,
`SUMMARIZER_MODEL_TYPE` and `MAX_TOKENS_FOR_RESPONSE`.
