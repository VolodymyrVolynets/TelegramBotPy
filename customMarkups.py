from telebot import types
class CustomMarkups():
    def cancelMarkup(self) -> types.ReplyKeyboardMarkup:
        markUp_keyboard = types.ReplyKeyboardMarkup()

        firstLineBt = types.KeyboardButton('Отмена')

        markUp_keyboard.row(firstLineBt)

        return markUp_keyboard

    # def cancelAndBackMarkup(self) -> types.ReplyKeyboardMarkup:
    #     markUp_keyboard = types.ReplyKeyboardMarkup()
    #
    #     firstLineFirstRow = types.KeyboardButton('Отмена')
    #     firstLineSecondRow = types.KeyboardButton('Назад')
    #
    #     markUp_keyboard.row(firstLineFirstRow, firstLineSecondRow)
    #
    #     return markUp_keyboard

    def standartMarkup(self) -> types.ReplyKeyboardMarkup:
        markUp_keyboard = types.ReplyKeyboardMarkup()

        firstLineFirstRow = types.KeyboardButton('Начало')
        secondLineFirstRow = types.KeyboardButton('Баланс')
        secondLineSecondRow = types.KeyboardButton('Карта')
        thirdLineFirstRow = types.KeyboardButton('О боте')

        markUp_keyboard.row(firstLineFirstRow)
        markUp_keyboard.row(secondLineFirstRow, secondLineSecondRow)
        markUp_keyboard.row(thirdLineFirstRow)

        return markUp_keyboard