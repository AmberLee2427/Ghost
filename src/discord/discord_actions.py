# discord_actions.py
import discord
import re

async def send_bot_reply(message, text_content, logger, mention_author=True):
    """
    Sends a reply to a message, handling character limits.
    """
    if not message or not text_content:
        return
    try:
        if len(text_content) > 2000:
            logger(f"Message too long ({len(text_content)}). Splitting.")
            parts = [text_content[i:i + 1990] for i in range(0, len(text_content), 1990)]
            await message.channel.send(f"{message.author.mention}", embed=discord.Embed(description=parts[0]))
            for part in parts[1:]:
                await message.channel.send(embed=discord.Embed(description=part))
        else:
            await message.reply(text_content, mention_author=mention_author)
    except discord.Forbidden:
        logger(f"Permissions Error in channel {message.channel.name}")
    except discord.HTTPException as e:
        logger(f"Failed to send message to {message.channel.name}: {e}")

async def process_special_commands(raw_response, message, logger):
    """
    Parses and executes special commands like @REACT_EMOJI and @TAG_USER.
    Returns the cleaned response text.
    """
    logger(f"DEBUG: process_special_commands received raw_response: '{raw_response}'") # ADD THIS LINE

    # Handle @TAG_USER
    def replace_tag_with_mention(match):
        user_id = match.group(1)
        return f'<@{user_id}>'

    processed_text = re.sub(r"@TAG_USER='(\d+)'", replace_tag_with_mention, raw_response)

    logger(f"DEBUG: After TAG_USER regex, processed_text: '{processed_text}'") # ADD THIS LINE

    # Handle @REACT_EMOJI
    react_match = re.search(r"@REACT_EMOJI='(.*?)'", processed_text)
    if react_match:
        emoji = react_match.group(1).strip()
        # Remove the command from the text to be sent
        processed_text = processed_text.replace(react_match.group(0), "").strip()
        try:
            await message.add_reaction(emoji)
            logger(f"Reacted with {emoji}.")
        except Exception as e:
            logger(f"Failed to add reaction '{emoji}': {e}")

    return processed_text