
from telethon.sync import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.errors import FloodWaitError
import time
import datetime
import sys
import re

API_ID = Тут ваш апи айди
API_HASH = "Ваш апи хэш"
PHONE = "Номер телефона с +"

SESSION_FILE = "mysession.session"
NICKNAMES_FILE = "Nicknames.txt"
BIO_FILE = "Bio.txt"

def load_nicknames():
    with open(NICKNAMES_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def load_bio_template():
    with open(BIO_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def get_utc10_time():
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=10)
    return now.strftime("%H:%M")

def create_client():
    return TelegramClient(SESSION_FILE, API_ID, API_HASH)

def connect_client(client):
    try:
        if client.is_connected():
            try:
                client.disconnect()
            except:
                pass
    except:
        pass

    for attempt in range(5):
        try:
            client.connect()
            if client.is_user_authorized():
                print("[CONNECT] Connected successfully")
                sys.stdout.flush()
                return True
            else:
                print("[CONNECT] Session expired, re-authorizing...")
                sys.stdout.flush()
                client.start(phone=PHONE)
                print("[CONNECT] Re-authorized successfully")
                sys.stdout.flush()
                return True
        except Exception as e:
            print("[CONNECT] Attempt {} failed: {}".format(attempt + 1, str(e)))
            sys.stdout.flush()
            time.sleep(10)

    return False

def main():
    print("Starting tg-nbc name/bio changer...")
    sys.stdout.flush()

    nicknames = load_nicknames()
    bio_template = load_bio_template()

    print("Loaded {} nicknames".format(len(nicknames)))
    sys.stdout.flush()

    client = create_client()
    if not connect_client(client):
        print("[FATAL] Could not connect, exiting")
        sys.stdout.flush()
        return

    nickname_index = 0
    last_updated_minute = None

    while True:
        try:
            current_minute = get_utc10_time()

            if current_minute == last_updated_minute:
                time.sleep(5)
                continue

            if not client.is_connected():
                print("[RECONNECT] Connection lost, reconnecting...")
                sys.stdout.flush()
                if not connect_client(client):
                    print("[RECONNECT] Failed, retrying in 15 seconds...")
                    sys.stdout.flush()
                    time.sleep(15)
                    continue

            new_bio = bio_template.replace("00:00", current_minute)
            new_name = nicknames[nickname_index]

            try:
                client(UpdateProfileRequest(about=new_bio, first_name=new_name))
                print("[UPDATE] {} | {} | {}".format(current_minute, new_name, new_bio))
                sys.stdout.flush()
                nickname_index = (nickname_index + 1) % len(nicknames)
                last_updated_minute = current_minute
            except FloodWaitError as e:
                print("[FLOOD] Wait {} seconds".format(e.seconds))
                sys.stdout.flush()
                time.sleep(e.seconds + 5)
                continue
            except Exception as e:
                error_msg = str(e)
                wait_match = re.search(r'wait of (\d+) seconds', error_msg)
                if wait_match:
                    wait_time = int(wait_match.group(1))
                    print("[RATE LIMIT] Wait {} seconds".format(wait_time))
                    sys.stdout.flush()
                    time.sleep(wait_time + 5)
                    continue
                print("[ERROR] {}".format(error_msg))
                sys.stdout.flush()
                time.sleep(10)
                continue

            time.sleep(30)

        except KeyboardInterrupt:
            print("\n[EXIT] Stopping...")
            sys.stdout.flush()
            try:
                client.disconnect()
            except:
                pass
            break
        except Exception as e:
            print("[MAIN ERROR] {}".format(str(e)))
            sys.stdout.flush()
            time.sleep(15)

            try:
                client.disconnect()
            except:
                pass

            client = create_client()
            if not connect_client(client):
                print("[MAIN ERROR] Reconnect failed, retrying...")
                sys.stdout.flush()
                time.sleep(15)

if __name__ == "__main__":
    main()
