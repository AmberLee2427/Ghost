# llm_handler.py
import google.generativeai as genai
import openai
from google.api_core.exceptions import GoogleAPIError
from google.generativeai.types import (
    BlockedPromptException,
    StopCandidateException,
)
from config import (
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    OPENAI_MODEL_NAME,
    GEMINI_MODEL_NAME,
    MAX_TOKENS_FOR_RESPONSE,
    BASE_TEMPERATURE,
)

# --- API and Model Initialization ---
oclient = openai.OpenAI(api_key=OPENAI_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

async def get_llm_response(
    model_type,
    system_prompt,
    history,
    user_prompt,
    logger,
    model_name=None,
):
    """
    Abstracts the API call to either OpenAI or Gemini.
    """
    try:
        if model_type == "openai":
            messages_payload = [
                {"role": "system", "content": system_prompt}
            ] + [
                {"role": "assistant" if m["role"] == "model" else "user", "content": m["content"]}
                for m in reversed(history)
            ] + [
                {"role": "user", "content": user_prompt}
            ]

            response = oclient.chat.completions.create(
                model=model_name or OPENAI_MODEL_NAME,
                messages=messages_payload,
                max_tokens=MAX_TOKENS_FOR_RESPONSE,
                temperature=BASE_TEMPERATURE,
            )
            return response.choices[0].message.content

        elif model_type == "gemini":
            gemini_model = genai.GenerativeModel(
                model_name or GEMINI_MODEL_NAME,
                system_instruction=system_prompt,
            )

            gemini_history = []
            for msg in reversed(history):
                role_for_gemini = "model" if msg["role"] == "model" else "user"
                # Merge consecutive user/model messages as required by Gemini API
                if gemini_history and gemini_history[-1]["role"] == role_for_gemini:
                    gemini_history[-1]["parts"][0] += f"\n\n{msg['content']}"
                else:
                    gemini_history.append({"role": role_for_gemini, "parts": [msg["content"]]})

            chat_session = gemini_model.start_chat(history=gemini_history)
            response = await chat_session.send_message_async(user_prompt)
            return response.text

        else:
            logger(f"!!! Unknown model_type '{model_type}'")
            return None

    except openai.OpenAIError as e:
        logger(f"!!! OpenAI API error: {e}")
    except (GoogleAPIError, BlockedPromptException, StopCandidateException) as e:
        logger(f"!!! Gemini API error: {e}")
    except Exception as e:
        logger(f"!!! Unexpected error using {model_type} model: {e}")

    return None
