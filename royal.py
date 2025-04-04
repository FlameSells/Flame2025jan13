import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import UserDeactivatedBanError, FloodWaitError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

# Define session folder
CREDENTIALS_FOLDER = 'sessions'
os.makedirs(CREDENTIALS_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename='og_flame_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Auto-Reply Message
AUTO_REPLY_MESSAGE = """
HEY SIR/MAM WELCOME TO ROYAL PLACE 🙌

Owner Of Royale: @theroyaleplace☄️
Our Store: @royalestoreb☄️
Our proofs: @royalproofsse☄️

If u need any type of help if i am offline or no available so u can dm also our admin @theroyaleplaces  ✅

Check Out Our Store For Exclusive Deals with us 👨‍💼

Thanks for deal with Royale ☺️
"""

def display_banner():
    """Display the banner using pyfiglet."""
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

def save_credentials(session_name, credentials):
    """Save session credentials to file."""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    """Load session credentials from file."""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

async def get_last_saved_message(client):
    """Retrieve the last message from 'Saved Messages'."""
    try:
        saved_messages_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(
            peer=saved_messages_peer,
            limit=1,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            max_id=0,
            min_id=0,
            hash=0
        ))
        return history.messages[0] if history.messages else None
    except Exception as e:
        logging.error(f"Failed to retrieve saved messages: {str(e)}")
        return None

async def forward_messages_to_groups(client, last_message, session_name, rounds, delay_between_rounds):
    """Forward the last saved message to all groups."""
    try:
        dialogs = await client.get_dialogs()
        group_dialogs = [dialog for dialog in dialogs if dialog.is_group]

        if not group_dialogs:
            logging.warning(f"No groups found for session {session_name}.")
            return

        print(Fore.CYAN + f"Found {len(group_dialogs)} groups for session {session_name}")

        for round_num in range(1, rounds + 1):
            print(Fore.YELLOW + f"\nStarting round {round_num} for session {session_name}...")

            for dialog in group_dialogs:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                    logging.info(f"Message forwarded to {group.title} using {session_name}")
                except FloodWaitError as e:
                    print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} after waiting.")
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
                    logging.error(f"Failed to forward message to {group.title}: {str(e)}")

                random_delay = random.randint(15, 30)
                print(Fore.CYAN + f"Waiting for {random_delay} seconds before next group...")
                await asyncio.sleep(random_delay)

            print(Fore.GREEN + f"Round {round_num} completed for session {session_name}.")
            if round_num < rounds:
                print(Fore.CYAN + f"Waiting for {delay_between_rounds} seconds before next round...")
                await asyncio.sleep(delay_between_rounds)
    except Exception as e:
        logging.error(f"Unexpected error in forward_messages_to_groups: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Set up auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"Replied to {event.sender_id} in session {session_name}")
                logging.info(f"Replied to {event.sender_id} in session {session_name}")
            except FloodWaitError as e:
                print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception as e:
                print(Fore.RED + f"Failed to reply to {event.sender_id}: {str(e)}")
                logging.error(f"Failed to reply to {event.sender_id}: {str(e)}")

async def create_and_save_client(session_name, api_id, api_hash):
    """Create client and save session after login."""
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start(
        phone=lambda: input(Fore.CYAN + "Enter phone number (with country code): "),
        code_callback=lambda: input(Fore.CYAN + "Enter OTP code: "),
        password=lambda: input(Fore.CYAN + "Enter 2FA password (if any): ")
    )
    
    # Save the session string
    session_string = StringSession.save(client.session)
    credentials = {
        "api_id": api_id,
        "api_hash": api_hash,
        "string_session": session_string
    }
    save_credentials(session_name, credentials)
    
    return client

async def main():
    """Main function to handle user input and execute the script."""
    display_banner()

    try:
        num_accounts = int(input("Enter number of accounts: "))
        if num_accounts <= 0:
            print(Fore.RED + "Number of accounts must be > 0")
            return

        valid_clients = []

        for i in range(1, num_accounts + 1):
            session_name = f"account{i}"
            credentials = load_credentials(session_name)

            if credentials:
                # Existing session found
                client = TelegramClient(
                    StringSession(credentials["string_session"]),
                    credentials["api_id"],
                    credentials["api_hash"]
                )
                await client.start()
                print(Fore.GREEN + f"Logged in via session for account {i}")
            else:
                # New login required
                api_id = int(input(Fore.CYAN + f"Enter API ID for account {i}: "))
                api_hash = input(Fore.CYAN + f"Enter API hash for account {i}: "))
                client = await create_and_save_client(session_name, api_id, api_hash)
                print(Fore.GREEN + f"Logged in via phone for account {i}")

            valid_clients.append((client, session_name))

        if not valid_clients:
            print(Fore.RED + "No valid accounts available")
            return

        print(Fore.MAGENTA + "\nChoose mode:")
        print(Fore.YELLOW + "1. Auto Forwarding")
        print(Fore.YELLOW + "2. Auto Reply")

        option = int(input(Fore.CYAN + "Enter choice: "))
        rounds, delay = 0, 0

        if option == 1:
            rounds = int(input(Fore.MAGENTA + "Enter number of forwarding rounds: "))
            delay = int(input(Fore.MAGENTA + "Enter delay between rounds (seconds): "))

            for round_num in range(1, rounds + 1):
                print(Fore.YELLOW + f"\nStarting round {round_num}")
                tasks = []
                for client, session_name in valid_clients:
                    last_msg = await get_last_saved_message(client)
                    if last_msg:
                        tasks.append(forward_messages_to_groups(client, last_msg, session_name, 1, 0))
                await asyncio.gather(*tasks)
                if round_num < rounds:
                    print(Fore.CYAN + f"Waiting {delay} seconds before next round...")
                    await asyncio.sleep(delay)

        elif option == 2:
            print(Fore.GREEN + "Starting Auto Reply mode...")
            tasks = [setup_auto_reply(client, session_name) for client, session_name in valid_clients]
            await asyncio.gather(*tasks)
            print(Fore.CYAN + "Auto-reply running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)

        for client, _ in valid_clients:
            await client.disconnect()

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped by user")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
