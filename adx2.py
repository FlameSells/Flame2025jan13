import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events, errors
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
⭐️   Please contact us In Official I’d  ⭐️

👇 OUR OFFICAL ID 👇

         @MR_XSHOP 
         @MR_XSHOP


🗿Why choose us ? 

* All video Fròm dark Web ✅
* Service provide since 2019 ✅
* Biggest & newest collection ✅ 
* Safest payment gateway fòr privacy ✅
* Each month 5 new updates inn all chanels ✅
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

async def forward_messages_to_groups(client, last_message, session_name):
    """Forward the last saved message to all groups with random delays."""
    try:
        dialogs = await client.get_dialogs()
        group_dialogs = [dialog for dialog in dialogs if dialog.is_group]

        if not group_dialogs:
            print(Fore.YELLOW + f"[{session_name}] No groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Found {len(group_dialogs)} groups")

        for dialog in group_dialogs:
            group = dialog.entity
            try:
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"[{session_name}] Forwarded to {group.title}")
                logging.info(f"[{session_name}] Forwarded to {group.title}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"[{session_name}] Forwarded after wait to {group.title}")
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Failed to forward to {group.title}: {str(e)}")
                logging.error(f"[{session_name}] Failed to forward to {group.title}: {str(e)}")

            # Random delay between 15-30 seconds
            delay = random.randint(15, 30)
            print(Fore.CYAN + f"[{session_name}] Waiting {delay} seconds before next group...")
            await asyncio.sleep(delay)

    except Exception as e:
        print(Fore.RED + f"[{session_name}] Forwarding error: {str(e)}")
        logging.error(f"[{session_name}] Forwarding error: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Set up auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Replied to {event.sender_id}")
                logging.info(f"[{session_name}] Replied to {event.sender_id}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Failed to reply: {str(e)}")
                logging.error(f"[{session_name}] Failed to reply: {str(e)}")

async def run_session(session_name, credentials):
    """Run both forwarding and auto-reply for a session."""
    client = TelegramClient(
        StringSession(credentials["string_session"]),
        credentials["api_id"],
        credentials["api_hash"]
    )
    
    try:
        await client.start()
        print(Fore.GREEN + f"[{session_name}] Successfully logged in")
        
        # Start auto-reply
        await setup_auto_reply(client, session_name)
        
        # Continuous forwarding with 15 minute intervals
        while True:
            last_message = await get_last_saved_message(client)
            if last_message:
                await forward_messages_to_groups(client, last_message, session_name)
            else:
                print(Fore.RED + f"[{session_name}] No saved message found")
            
            print(Fore.YELLOW + f"[{session_name}] Waiting 15 minutes before next round...")
            await asyncio.sleep(900)  # 15 minutes
            
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Account banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Error: {str(e)}")
    finally:
        await client.disconnect()

async def login_with_phone(session_name):
    """Handle phone login with OTP and 2FA."""
    while True:
        try:
            print(Fore.CYAN + f"\nLogin for {session_name}:")
            phone = input("Phone number (with country code): ").strip()
            api_id = int(input("API ID: ").strip())
            api_hash = input("API Hash: ").strip()
            
            client = TelegramClient(f"sessions/{session_name}", api_id, api_hash)
            await client.connect()
            
            # Send code request
            await client.send_code_request(phone)
            print(Fore.GREEN + "Verification code sent")
            
            # Handle code input
            while True:
                code = input('Enter the code (or "r" to resend): ').strip()
                if code.lower() == 'r':
                    await client.send_code_request(phone)
                    print(Fore.GREEN + "New code sent")
                    continue
                
                try:
                    await client.sign_in(phone, code)
                    break
                except errors.PhoneCodeInvalidError:
                    print(Fore.RED + "Wrong code! Try again")
                except errors.PhoneCodeExpiredError:
                    print(Fore.RED + "Code expired. Sending new code...")
                    await client.send_code_request(phone)
                    print(Fore.GREEN + "New code sent")
                except errors.SessionPasswordNeededError:
                    print(Fore.YELLOW + "2FA password required")
                    while True:
                        password = input("Enter your 2FA password: ")
                        try:
                            await client.sign_in(password=password)
                            break
                        except errors.PasswordHashInvalidError:
                            print(Fore.RED + "Wrong password! Try again")
            
            # Verify login success
            if await client.is_user_authorized():
                me = await client.get_me()
                print(Fore.GREEN + f"Successfully logged in as {me.first_name}")
                string_session = client.session.save()
                await client.disconnect()
                return {
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "string_session": string_session
                }
            
        except Exception as e:
            print(Fore.RED + f"Login error: {str(e)}")
            if 'client' in locals():
                await client.disconnect()
            print(Fore.YELLOW + "Let's try again...")

async def main():
    """Main function to handle user input and execute the script."""
    display_banner()

    try:
        num_sessions = int(input("Enter number of sessions: "))
        if num_sessions <= 0:
            print(Fore.RED + "Number must be greater than 0")
            return

        tasks = []
        
        for i in range(1, num_sessions + 1):
            session_name = f"session{i}"
            credentials = load_credentials(session_name)

            if not credentials:
                credentials = await login_with_phone(session_name)
                save_credentials(session_name, credentials)

            tasks.append(run_session(session_name, credentials))

        print(Fore.GREEN + "\nStarting all sessions (Auto-Reply + Forwarding)...")
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped by user")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")
