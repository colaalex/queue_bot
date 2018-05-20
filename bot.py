from telebot import types, TeleBot
from collections import OrderedDict
import json


bot = TeleBot('INSERT TOKEN')
bot_username = 'INSERT BOT USERNAME'
queues = OrderedDict()


def read_json():
    global queues
    with open('queues.json') as f:
        queues = OrderedDict(json.loads(f.read()))


def write_json():
    with open('queues.json', 'w') as f:
        f.write(json.dumps(queues))


@bot.message_handler()
def wrong_door(msg):
    bot.send_message(msg.chat.id, 'Я не работаю в личной переписке. Очередь - это когда минимум 2 человека. Введи '
                                  '@{} в чате и радуйся!'.format(bot_username))


@bot.inline_handler(func=lambda chosen_inline_result: True)
def get_msg(query):
    try:
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton('Встать в очередь', callback_data='enter_' + query.query))
        key1 = types.InlineKeyboardMarkup()
        key1.add(types.InlineKeyboardButton('Встать в очередь', callback_data='enter1_' + query.query))
        queue = types.InlineQueryResultArticle(id='1', title='Создать очередь', description='Очередь на '+query.query,
                                               input_message_content=types.InputTextMessageContent(
                                                   message_text='Очередь на *'+query.query+'*',
                                                   parse_mode='Markdown'
                                               ), reply_markup=key)
        queue1 = types.InlineQueryResultArticle(id='2', title='Создать очередь', description='Очередь в '+query.query,
                                                input_message_content=types.InputTextMessageContent(
                                                    message_text='Очередь в *'+query.query+'*',
                                                    parse_mode='Markdown'
                                                ), reply_markup=key1)
        bot.answer_inline_query(query.id, [queue, queue1])
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('enter'))
def enter_queue(call):
    prep = 'на' if call.data.startswith('enter_') else 'в'
    subj = call.data.split('_')[1]
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton('Встать в очередь', callback_data=call.data))
    if call.inline_message_id not in queues:  # проверка нахождения очереди в списке текущих очередей
        # если при нажатии кнопки очереди в списке не было, добавим в список очередь с первым человеком в ней
        # каждая очередь - словарь участников очереди. Каждый участник очереди - пара ключ-значение, где ключ - id в тг
        # значение - кортеж из его имени и фамилии
        queues[call.inline_message_id] = OrderedDict(
            [(str(call.from_user.id), (call.from_user.first_name, call.from_user.last_name))])
        last_name = '' if call.from_user.last_name is None else call.from_user.last_name  # не выводим фамилию если None
        text = 'Очередь {} *{}*\n1. {} {}'.format(prep, subj, call.from_user.first_name, last_name)
        write_json()
        bot.edit_message_text(text, inline_message_id=call.inline_message_id, reply_markup=key, parse_mode='Markdown')
    else:
        if str(call.from_user.id) not in queues[call.inline_message_id]:
            queues[call.inline_message_id].update({str(call.from_user.id): (call.from_user.first_name, call.from_user.last_name)})
            queues[call.inline_message_id].move_to_end(str(call.from_user.id))
            text = 'Очередь {} *{}*\n'.format(prep, subj)
            n = 1
            for i in queues[call.inline_message_id]:
                first_name, last_name = queues[call.inline_message_id][i][0], queues[call.inline_message_id][i][1]
                last_name = '' if last_name is None else last_name
                text += '{}. {} {}\n'.format(n, first_name, last_name)
                n += 1
            write_json()
            bot.edit_message_text(text, inline_message_id=call.inline_message_id, reply_markup=key, parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, 'Ты уже в очереди', False)


if __name__ == '__main__':
    read_json()
    bot.polling(none_stop=True, timeout=7200)
