import requests

def send_telegram_message(bot_token, chat_id, message):
    """
    Sends a message via the Telegram Bot API.

    Args:
        bot_token (str): The token obtained from BotFather.
        chat_id (str): The chat ID of the user or group to send the message to.
        message (str): The text message to send.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Message sent successfully!")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message. Error: {e}")
        return None

if __name__ == "__main__":
    # Replace with your actual credentials
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    CHAT_ID = "TARGET_CHAT_ID_HERE"
    TEXT = "Hello! Yeh message API ke through bheja gaya hai."

    send_telegram_message(TOKEN, CHAT_ID, TEXT)
