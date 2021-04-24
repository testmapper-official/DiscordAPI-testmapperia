from discord.ext import commands
from mapsAPI import *
from WeatherForecastAPI import *
import sqlite3

TOKEN = 'Njk1NzA5MjEwMTA4NzU1OTc5.XoeIWw.1qVGrnNiAUB7mjPEqLHW5cUepvE'
MAPS = {'ll': (None, None),
        'points': [],
        'z': 3,
        'type': 'map'
        }
SQL_map = None

bot = commands.Bot(command_prefix='t!')
bot.remove_command('help')


# возвращает готовую карту с точками и комментариями.
def get_map(maps):
    link = get_link(maps)
    desc = ''
    if maps['points']:
        for i in range(len(maps['points'])):
            desc += f'''\n • {i + 1}.  Поисковое имя: {maps['points'][i]['name']}  \
            Координаты: {maps['points'][i]['coords']} \
            Комментарий: {maps['points'][i]['description']}'''
    else:
        desc = 'Вот, чистая карта'
    return desc + '\n' + link


# Бот готов к использованию.
@bot.event
async def on_ready():
    print('Connection has been successful!')


@bot.command(pass_context=False)
async def help(ctx):
    message = """Список доступных команд на боте ***testmapperia***: ```
!hello : послать привет боту
!create_map : создать карту по поисковому запросу. e.x. - !create_map Москва.
!set_zoom : установить высоту камеры на карте. От 0 до 23. !set_zoom 13.
!add_point : создает точку по поисковому запросу. e.x. - !add_point Москва.
!del_point : удаляет точку по существующему номеру. e.x. - !del_point 1.
!edit_point : изменяет параметры точки по существующему номеру (coords, name, description).
 e.x. - !edit_point 1 description Столица России. По параметру change_place меняет местоположение точки по поисковому
 запросу.
!move_to : размещает карту по центру указанного объекта по поисковому запросу. e.x. - !move_to Москва. Также можно
переместиться к существующим точкам. e.x. - !move_to point 1
!set_type : устанавливает тип карты (map; sat; sat,skl; sat,trf,skl; map,trf,skl). e.x. - !set_type sat.
!show_map : показывает открытую на данный момент карту.
!show_points : показывает существующие точки на карте.
!open_map : загружает из базы данных карту по названию, если текущая закрыта. e.x. - !open_map Netherlands.
!del_map : удаляет из базы данных карту по названию, если текущая закрыта. e.x. - !del_map Moscow.
!close_map : закрывает текущую карту.
!maplist : показывает список сохраненных карт в базе данных.
!save_map : сохраняет карту в базу данных, если название не указано, то сохраняет как untitled. e.x. - !save_map 
Netherlands.
!cur_forecast_in : показать информацию погоды на сегодняшний день в указанном объекте (не учитываются области и 
выше). e.x. - !cur_forecast_in Москва. Также можно узнать погоду в центре карты или указанной точке. e.x. -
!cur_forecast_in map или !cur_forecast_in map point 1.
!forecast_in : аналогичная команде !cur_forecast_in, но показываются первые N следующие дни. e.x. - !forecast_in 5
Москва.
Приятного развлечения с ботом!
```"""
    await ctx.send(message)


# Бот посылает привет с упоминанием пользователя.
@bot.command(pass_context=False)
async def hello(ctx):
    await ctx.send(f'Привет, {ctx.message.author.mention}!')


# Бот создает новую карту
@bot.command(pass_context=True)
async def create_map(ctx, *text):
    global MAPS
    if any(MAPS['ll']):
        await ctx.send('Карта уже существует. Удалите ее, чтобы создать новую.')
        return
    MAPS['ll'] = (get_coordinates(' '.join(text)))
    await ctx.send(get_map(MAPS))


# Установить высоту камеры на карте.
@bot.command(pass_context=True)
async def set_zoom(ctx, text):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return

    if text.isdigit() and 0 <= int(text) <= 23:
        MAPS['z'] = text
        await ctx.send(get_map(MAPS))
    elif text.isdigit():
        await ctx.send(f'{ctx.message.author.mention}, Я тебе блин русским языком говорю, что от 0 до 23!')
    else:
        await ctx.send(f'Неправильная осанка, сеньор {ctx.message.author.mention}!')


# Создает точку на карте.
@bot.command(pass_context=True)
async def add_point(ctx, *text):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return

    try:
        kwargs = {'name': ' '.join(text),
                  'coords': get_coordinates(' '.join(text)),
                  'description': ''
                  }
        MAPS['points'].append(kwargs)
        await ctx.send(get_map(MAPS))
    except Exception:
        await ctx.send(f'{ctx.message.author.mention}, Вы гений.')


# Удаляет точку на карте.
@bot.command(pass_context=True)
async def del_point(ctx, text):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return

    if text.isdigit() and 1 <= int(text) <= len(MAPS['points']):
        MAPS['points'].pop(int(text) - 1)
        await ctx.send(get_map(MAPS))
    elif text.isdigit():
        await ctx.send(f'{ctx.message.author.mention}, эта точка уже находится в черной дыре.')
    else:
        await ctx.send(f'Вы когда-нибудь научитесь писать русскими числами, {ctx.message.author.mention}?')


# Изменяет параметры точки на карте.
@bot.command(pass_context=True)
async def edit_point(ctx, *text):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return
    if text[0].isdigit() and 1 <= int(text[0]) <= len(MAPS['points']):
        try:
            if text[1] != 'coords' and text[1] != 'change_place':
                MAPS['points'][int(text[0]) - 1][text[1]] = ' '.join(text[2:])
            elif text[1] == 'change_place':
                MAPS['points'][int(text[0]) - 1]['name'] = ' '.join(text[2:])
                MAPS['points'][int(text[0]) - 1]['coords'] = get_coordinates(' '.join(text[2:]))
            else:
                MAPS['points'][int(text[0]) - 1][text[1]] = (float(text[2]), float(text[3]))
            await ctx.send(get_map(MAPS))
        except Exception as e:
            await ctx.send(f'{ctx.message.author.mention}, Вы облажались с правильным форматом.')
    elif text[0].isdigit():
        await ctx.send(f'{ctx.message.author.mention}, эта точка уже находится в черной дыре.')
    else:
        await ctx.send(f'Вы когда-нибудь научитесь писать русскими числами, {ctx.message.author.mention}?')


# Перемещает центр карты к указанной точке или месту.
@bot.command(pass_context=True)
async def move_to(ctx, *text):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return
    if text[0] == 'point':
        if text[1].isdigit() and 1 <= int(text[1]) <= len(MAPS['points']):
            MAPS['ll'] = MAPS['points'][int(text[1]) - 1]['coords']
            await ctx.send(get_map(MAPS))
        else:
            await ctx.send(f'{ctx.message.author.mention}, Эта точка уже давно в щели!')
    else:
        MAPS['ll'] = (get_coordinates(' '.join(text)))
        await ctx.send(get_map(MAPS))


# Устанавливает тип карты.
@bot.command(pass_context=True)
async def set_type(ctx, text):
    global MAPS
    if any(text == i for i in ['sat', 'map', 'sat,skl', 'sat,trf,skl', 'map,trf,skl']):
        MAPS['type'] = text
        await ctx.send(get_map(MAPS))
    else:
        await ctx.send(f'{ctx.message.author.mention}, Неверный тип карты. Или вы колобок)')


# Показывает открытую карту.
@bot.command(pass_context=False)
async def show_map(ctx):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return

    await ctx.send(get_map(MAPS))


# Показывает список отмеченных точек на карте.
@bot.command(pass_context=False)
async def show_points(ctx):
    global MAPS

    if not any(MAPS['ll']):
        await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
        return

    if MAPS['points']:
        s = f'{ctx.message.author.mention}, Список «черных» точек на вашей спине:'
        for i in range(len(MAPS['points'])):
            s += f'''\n • {i + 1}.  Поисковое имя: {MAPS['points'][i]['name']}  \
            Координаты: {MAPS['points'][i]['coords']} \
            Комментарий: {MAPS['points'][i]['description']}'''
        await ctx.send(s)
    else:
        await ctx.send(f'Ваша спина чиста, {ctx.message.author.mention}')


# открывает карту из базы данных.
@bot.command(pass_context=True)
async def open_map(ctx, text=None):
    global MAPS
    global SQL_map

    if any(MAPS['ll']):
        await ctx.send('Вы осмелились бросить своего лучшего друга Карту! Сохраните его честь и достоинство.')
        return

    if text:
        con = sqlite3.connect('DiscordData.sqlite')
        try:
            cur = con.cursor()
            que = f"SELECT * from maps where (name='{text}');"
            curmap = cur.execute(que).fetchall()[0]
            SQL_map = curmap[0]
            MAPS['ll'] = (curmap[2], curmap[3])
            MAPS['z'] = curmap[4]
            MAPS['type'] = curmap[5]
            que = f"SELECT * from points where (map_id='{SQL_map}');"
            points = cur.execute(que).fetchall()
            for point in points:
                MAPS['points'].append({'name': point[2],
                                       'coords': (point[3], point[4]),
                                       'description': point[5]
                                       })

            await ctx.send(get_map(MAPS))

        except sqlite3.Error:
            await ctx.send(f'{ctx.message.author.mention}? Такой карты нет.')
        except Exception:
            await ctx.send(f'Вероятно, вы где-то накосячили,  {ctx.message.author.mention}.')
        con.close()

    else:
        await ctx.send(f'Ты издеваешься, {ctx.message.author.mention}? У меня карт куча, тебе их все открыть?')


# удаляет карты из базы данных.
@bot.command(pass_context=True)
async def del_map(ctx, text):
    global MAPS

    if any(MAPS['ll']):
        await ctx.send('Перед тем как что-то удалять, закройте карту.')
        return

    if text:
        con = sqlite3.connect('DiscordData.sqlite')
        try:
            cur = con.cursor()
            que = f"DELETE from maps where (name='{text}');"
            cur.execute(que)
            con.commit()

            await ctx.send(f'{ctx.message.author.mention}, карта была успешно удалена')

        except sqlite3.Error:
            await ctx.send(f'{ctx.message.author.mention}? Такой карты похоже уже нет.')
        con.close()

    else:
        await ctx.send(f'Ты издеваешься, {ctx.message.author.mention}? У меня карт куча, тебе их все удалить?')


# закрывает карту.
@bot.command(pass_context=False)
async def close_map(ctx):
    global MAPS
    global SQL_map

    if not any(MAPS['ll']):
        await ctx.send('Вы только что попытались закрыть воздух. Произошел временной парадокс.')
        return

    try:
        MAPS = {'ll': (None, None),
                'points': [],
                'z': 3,
                'type': 'map'
                }
        SQL_map = None
    finally:
        await ctx.send('Карта была успешна закрыта.')


# показывает список сохраненных карт.
@bot.command(pass_context=False)
async def maplist(ctx):
    con = sqlite3.connect('DiscordData.sqlite')
    try:
        cur = con.cursor()
        que = f"SELECT name from maps;"
        names = cur.execute(que).fetchall()
        string = 'Список сохраненных карт:'
        for i in names:
            string += f'\n • {i[0]}'
        await ctx.send(string)
    except Exception:
        await ctx.send(f'Произошла ошибка. Попробуйте еще раз.')
    con.close()


# сохраняет карту в базу данных.
@bot.command(pass_context=True)
async def save_map(ctx, text='untitled'):
    global MAPS
    global SQL_map

    if not any(MAPS['ll']):
        await ctx.send('Для начала нужно эксплуатировать Дашу для поиска карты.')
        return

    con = sqlite3.connect('DiscordData.sqlite')

    cur = con.cursor()
    try:
        que = f"SELECT id from maps where (name='{text}');"
        SQL_map = [i[0] for i in cur.execute(que).fetchall()][0]
    except:
        pass
    if SQL_map is not None:
        que = f"SELECT id from maps where (name='{text}');"
        if cur.execute(que).fetchall():
            SQL_map = [i[0] for i in cur.execute(que).fetchall()][0]
            que = f"""DELETE from points where map_id={SQL_map}"""
            cur.execute(que)
            que = f"""DELETE from maps where id={SQL_map}"""
            cur.execute(que)
            con.commit()
    que = f"INSERT INTO maps (name, x, y, z, type) VALUES ('{text}', {MAPS['ll'][0]}, {MAPS['ll'][1]}, \
    {MAPS['z']}, '{MAPS['type']}');"
    cur.execute(que)
    que = f"SELECT id from maps WHERE (name='{text}');"
    SQL_map = [i[0] for i in cur.execute(que).fetchall()][0]
    if MAPS['points']:
        for i in range(len(MAPS['points'])):
            que = f"""INSERT INTO points (map_id, name, x, y, description) VALUES ({SQL_map}, '{MAPS['points'][i]['name']}',
                {MAPS['points'][i]['coords'][0]}, {MAPS['points'][i]['coords'][1]},
                '{MAPS['points'][i]['description']}');"""
            cur.execute(que)
    con.commit()
    await ctx.send(f'{ctx.message.author.mention}, Карта успешно была сохранена под названием {text}')
    con.close()


@bot.command(pass_context=False)
async def cur_forecast_in(ctx, *text):
    global MAPS
    try:
        if text[0] == 'map':
            if not any(MAPS['ll']):
                await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
                return
            if len(text) >= 2:
                if text[1] == 'point' and text[2].isdigit() and 1 <= int(text[2]) <= len(MAPS['points']):
                    response = weather_response(MAPS['points'][int(text[2]) - 1]['coords'])
                    message = current_weather(response)
                    await ctx.send(message)
                else:
                    await ctx.send(f'{ctx.message.author.mention}, такой точки не существует.')
            else:
                response = weather_response(MAPS['ll'])
                message = current_weather(response)
                await ctx.send(message)
        else:
            text = ' '.join(text)
            response = weather_response(text)
            message = current_weather(response)
            await ctx.send(message)
    except Exception:
        await ctx.send(f'{ctx.message.author.mention}, Неправильный формат ввода.')


@bot.command(pass_context=True)
async def forecast_in(ctx, days, *text):
    try:
        if text[0] == 'map':
            if not any(MAPS['ll']):
                await ctx.send('Жулик своровал карту. Давайте позовем Дашу поискать его.')
                return
            if len(text) >= 2:
                if text[1] == 'point' and text[2].isdigit() and 1 <= int(text[2]) <= len(MAPS['points']):
                    message = forecast_weather(weather_response(MAPS['points'][int(text[2]) - 1]['coords']), int(days))
                    await ctx.send(message)
                else:
                    await ctx.send(f'{ctx.message.author.mention}, такой точки не существует.')
            else:
                message = forecast_weather(weather_response(MAPS['ll']), int(days))
                await ctx.send(message)
        else:
            text = ' '.join(text)
            message = forecast_weather(weather_response(text), int(days))
            await ctx.send(message)
    except Exception:
        await ctx.send(f'{ctx.message.author.mention}, Неправильный формат ввода.')


# Запуск бота на орбиту TOKEN.
bot.run(TOKEN)
