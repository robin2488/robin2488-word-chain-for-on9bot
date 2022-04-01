# pip install telethon
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityMentionName
import asyncio
from collections import defaultdict
import random, time, sys

# On first run it will ask for your phone number and confirmation code to log in
# It will save the file SESSION_NAME.session to store the information and so it doesn't need to ask again next time
# API ID and hash are the ones I created on https://my.telegram.org, you can create your own or use this
SESSION_NAME = 'test'
API_ID = 17764502
API_HASH = '17563e75fad756f25f30baba831a9860'

ALL_WORDS = {}
def load_words(chat_id):
    ALL_WORDS[chat_id] = defaultdict(list)
    with open('Words.txt', 'r') as f:
        for line in f.readlines():
            word = line[:-1].lower()
            if only_alpha(word):
                ALL_WORDS[chat_id][line[0]].append(word)

def only_alpha(word):
    for c in word:
        if not c.isalpha():
            return False
    return True

def contains(word, letters):
    for l in letters:
        if l in word:
            return True
    return False

def find_words(chat_id, start_letter, min_length, spam=None, required=None, forbidden=None, ban_endings=None):
    if not chat_id in ALL_WORDS:
        load_words(chat_id)

    words = []
    for word in ALL_WORDS[chat_id][start_letter]:
        if len(word) >= int(min_length):
            if not required or contains(word, required):
                if not forbidden or not contains(word, forbidden):
                    if not spam or word[-1] == spam:
                        if not ban_endings or not word[-1] in ban_endings:
                            words.append(word)

    if len(words) == 0:
        if spam:
            return find_words(chat_id, start_letter, min_length, None, required, forbidden, ban_endings)
        elif ban_endings:
            return find_words(chat_id, start_letter, min_length, spam, required, forbidden, None)

    return words

def choose_word(words):
    if len(words) > 0:
        return random.choice(words)
    else:
        return ''

def remove_word(chat_id, word):
    word = word.lower()
    if chat_id in ALL_WORDS:
        if word in ALL_WORDS[chat_id][word[0]]:
            ALL_WORDS[chat_id][word[0]].remove(word)

spam_letter = None
ban_endings = None

async def main():
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        user_id = (await client.get_me()).id
        @client.on(events.NewMessage(from_users='@on9wordchainbot', pattern='Game is starting...'))
        async def handler(event):
            load_words(event.message.chat_id)

        @client.on(events.NewMessage(from_users='@on9wordchainbot', pattern='Turn: '))
        async def handler(event):
            text = event.message.message
            entities = event.message.entities
            chat_id = event.message.chat_id
            if entities[0].user_id == user_id:
                line = text.split('\n')[1].split(' ')
                required = None
                forbidden = None

                if ', include' in text:
                    required = [c[0].lower() for c in line[7:-5]]

                if 'exclude' in text:
                    forbidden = [c[0].lower() for c in line[7:-6]]

                start_letter = line[5][0].lower()
                min_length = line[-2]

                matching = find_words(chat_id, start_letter, min_length, spam_letter, required, forbidden, ban_endings)
                chosen = choose_word(matching)

                time.sleep(random.randint(6,11))
                await client.send_message(event.message.peer_id, chosen)

        @client.on(events.NewMessage(from_users='@on9wordchainbot', pattern='.+ is accepted'))
        async def handler(event):
            remove_word(event.message.chat_id, event.message.message.split(' ')[0])

        @client.on(events.NewMessage(from_users='@on9wordchainbot', pattern='The first word is'))
        async def handler(event):
            remove_word(event.message.chat_id, event.message.message.split('\n')[0].split(' ')[4][:-1])

        @client.on(events.NewMessage(from_users='me', pattern='spam .'))
        async def handler(event):
            global spam_letter
            spam_letter = event.message.message[5]
            await event.reply(f'Spam {spam_letter} ending')

        @client.on(events.NewMessage(from_users='me', pattern='no spam'))
        async def handler(event):
            global spam_letter
            spam_letter = None
            await event.reply(f'No spam ending')

        @client.on(events.NewMessage(from_users='me', pattern='ban .+'))
        async def handler(event):
            global ban_endings
            ban_endings = event.message.message[4:].replace(' ', '')
            await event.reply(f'Ban {" ".join(ban_endings)} ending{"s" if len(ban_endings) > 1 else ""}')

        @client.on(events.NewMessage(from_users='me', pattern='no ban'))
        async def handler(event):
            global ban_endings
            ban_endings = None
            await event.reply(f'No banned endings')

        await client.run_until_disconnected()

asyncio.run(main())
