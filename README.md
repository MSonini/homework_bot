# yatube_project
### Описание
Телеграм-бот для проверки статуса домашнего задания. Программа периодически отправляет запрос к API Яндекс.Практикума, если статус работы изменился, то отправляет пользователю сообщение о текущем статусе.
### Технологии
 - Python 3.9
 - python-telegram-bot 13.7

### Запуск 
1. Скопировать репозиторий на компьютер.
2. Установить зависимости из файла requirements.txt.
3. Создать .env файл и в нем записать три константы следующим образом:
```
TELEGRAM_TOKEN=*ваш токен для Clien API в Телеграм*
PRACTICUM_TOKEN=*ваш токен от Яндекс.Практикум*
TELEGRAM_CHAT_ID=*ваш id чата в телеграм*
```
4. Запустить программу.

### Автор
Сонин Михаил
