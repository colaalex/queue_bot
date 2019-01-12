import json
import logging
from collections import OrderedDict

import cherrypy
from telebot import types, TeleBot, logger

import config
from server import WebhookServer as Serv

log = logger
log.setLevel(logging.INFO)

bot = TeleBot(config.token)
queues = OrderedDict()


def read_json():
    global queues
    with open('queues.json') as f:
        queues = OrderedDict(json.loads(f.read()))
    for q in queues:
        queues[q] = OrderedDict(queues[q])


def write_json():
    with open('queues.json', 'w') as f:
        f.write(json.dumps(queues))


# bot main logic
@bot.message_handler()
def wrong_door(msg):
    bot.send_message(msg.chat.id, 'Я не работаю в личной переписке. Очередь - это когда минимум 2 человека. Введи '
                                  '@{} в чате и радуйся!'.format(config.username))


@bot.inline_handler(func=lambda chosen_inline_result: True)
def get_msg(query: types.InlineQuery):
    """
    Срабатывает, когда пользователь вводит @bot_username <запрос>, предлагает варианты очередей с заданным запросом
    :param query: текст запроса
    """
    try:
        prepositions = ['на', 'в', 'за']
        answers = []

        for p in enumerate(prepositions):
            key = types.InlineKeyboardMarkup()
            key.add(types.InlineKeyboardButton(text='Встать в очередь',
                                               callback_data='enter_{}_{}'.format(p[1], query.query)))
            answers.append(types.InlineQueryResultArticle(id=str(p[0] + 1),
                                                          title='Создать очередь',
                                                          description='Очередь {} {}'.format(p[1], query.query),
                                                          input_message_content=types.InputTextMessageContent(
                                                              message_text='Очередь {} *{}*'.format(p[1], query.query),
                                                              parse_mode='Markdown'
                                                          ),
                                                          reply_markup=key))

        bot.answer_inline_query(query.id, answers)
    except Exception as e:
        print(e)


@bot.callback_query_handler(func=lambda call: call.data.startswith('enter'))
def enter_queue(call: types.CallbackQuery):
    """
    Срабатывает при нажатии кнопки "Встать в очередь", не добавляет, если уже в очереди
    :param call: callback от кнопки
    """
    action, prep, subj = call.data.split('_')
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton('Встать в очередь', callback_data=call.data))
    if call.inline_message_id not in queues:
        # проверка нахождения очереди в списке текущих очередей
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
            queues[call.inline_message_id].update({str(call.from_user.id): (call.from_user.first_name,
                                                                            call.from_user.last_name)})
            queues[call.inline_message_id].move_to_end(str(call.from_user.id))
            text = 'Очередь {} *{}*\n'.format(prep, subj)
            n = 1
            for i in queues[call.inline_message_id]:
                first_name, last_name = queues[call.inline_message_id][i][0], queues[call.inline_message_id][i][1]
                last_name = '' if last_name is None else last_name
                text += '{}. {} {}\n'.format(n, first_name, last_name)
                n += 1
            write_json()
            bot.edit_message_text(text, inline_message_id=call.inline_message_id,
                                  reply_markup=key, parse_mode='Markdown')
        else:
            bot.answer_callback_query(call.id, 'Ты уже в очереди', False)


bot.remove_webhook()
bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH,
                certificate=open(config.WEBHOOK_SSL_CERT))

cherrypy.quickstart(Serv(bot), config.WEBHOOK_URL_PATH, {'/': {}})
