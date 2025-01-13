import asyncio
import os
import json
import random
import logging
import socket
from telethon import TelegramClient, events, errors
from telethon.errors import SessionPasswordNeededError, UserDeactivatedBanError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

CREDENTIALS_FOLDER = 'sessions'

if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Set up logging
logging.basicConfig(
    filename='og_flame_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Updated Auto-Reply Message
AUTO_REPLY_MESSAGE = """
𝙞𝙩𝙨 𝙖𝙙𝙨 𝙖𝙘𝙘𝙤𝙪𝙣𝙩 𝙬𝙤𝙧𝙠𝙞𝙣𝙜 𝙛𝙤𝙧 @streamxify 𝙙𝙢 𝙛𝙤𝙧 @streamxify 𝙙𝙚𝙖𝙡𝙨 !!
"""

# Save session credentials to a file
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump(credentials, f)

# Load session credentials from file
def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

async def forward_messages_to_groups(client, last_message, session_name, rounds, delay_between_rounds):
    for round_num in range(1, rounds + 1):
        print(Fore.YELLOW + f"\nStarting round {round_num} for session {session_name}...")
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                    logging.info(f"Message forwarded to {group.title} using {session_name}")
                except errors.FloodWaitError as e:
                    print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
        if round_num < rounds:
            print(Fore.CYAN + f"Waiting {delay_between_rounds} seconds before next round...")
            await asyncio.sleep(delay_between_rounds)

async def auto_reply(client, session_name):
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            await event.reply(AUTO_REPLY_MESSAGE)
            print(Fore.GREEN + f"Replied to message from {event.sender_id} in session {session_name}")
            logging.info(f"Replied to message from {event.sender_id} in session {session_name}")
    await client.run_until_disconnected()

async def login_and_execute(api_id, api_hash, phone_number, session_name, option, rounds, delay_between_rounds):
    client = TelegramClient(session_name, api_id, api_hash)
    try:
        await client.start(phone=phone_number)

        if not await client.is_user_authorized():
            try:
                await client.send_code_request(phone_number)
                print(Fore.YELLOW + f"OTP sent to {phone_number}")
                otp = input(Fore.CYAN + f"Enter the OTP for {phone_number}: ")
                await client.sign_in(phone_number, otp)
            except SessionPasswordNeededError:
                password = input("Two-factor authentication enabled. Enter your password: ")
                await client.sign_in(password=password)

        print(Fore.GREEN + f"Logged in successfully for session {session_name}")

        saved_messages_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(peer=saved_messages_peer, limit=1, offset_id=0))

        if not history.messages:
            print(Fore.RED + "No messages found in 'Saved Messages'")
            return

        last_message = history.messages[0]

        if option == 1:
            await forward_messages_to_groups(client, last_message, session_name, rounds, delay_between_rounds)
        elif option == 2:
            await send_and_remove_groups(client, last_message, session_name)
        await auto_reply(client, session_name)
    except UserDeactivatedBanError:
        print(Fore.RED + f"Account {session_name} is banned.")
    except Exception as e:
        print(Fore.RED + f"Unexpected error in session {session_name}: {str(e)}")
    finally:
        await client.disconnect()

async def send_and_remove_groups(client, last_message, session_name):
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group = dialog.entity
            try:
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"Message sent to {group.title} using {session_name}")
            except Exception as e:
                print(Fore.RED + f"Failed to send to {group.title}. Removing group.")
                await client(LeaveChannelRequest(group))

async def main():
    display_banner()

    num_sessions = int(input("Enter how many sessions you want to log in: "))
    sessions = []

    for i in range(1, num_sessions + 1):
        session_name = f'session{i}'
        credentials = load_credentials(session_name)

        if credentials:
            api_id = credentials['api_id']
            api_hash = credentials['api_hash']
            phone_number = credentials['phone_number']
        else:
            api_id = int(input(f"Enter API ID for session {i}: "))
            api_hash = input(f"Enter API hash for session {i}: ")
            phone_number = input(f"Enter phone number for session {i} (with country code): ")
            save_credentials(session_name, {'api_id': api_id, 'api_hash': api_hash, 'phone_number': phone_number})

        sessions.append((api_id, api_hash, phone_number, session_name))

    print("\nSelect the action to perform for all accounts:")
    print("1. Forward last saved message to all groups (with rounds and delays)")
    print("2. Send last saved message to groups and remove failed ones")
    option = int(input("Enter your choice: "))

    rounds = delay_between_rounds = None
    if option == 1:
        rounds = int(input("Enter how many times to forward messages for all sessions: "))
        delay_between_rounds = int(input("Enter delay (in seconds) between rounds: "))

    tasks = [login_and_execute(api_id, api_hash, phone_number, session_name, option, rounds, delay_between_rounds)
             for api_id, api_hash, phone_number, session_name in sessions]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
