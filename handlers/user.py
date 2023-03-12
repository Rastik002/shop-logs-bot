from aiogram import Bot, types, Dispatcher
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from create_bot import dp, bot
from misc.keyboards import *
from misc.config import *
from misc.database import *
from random import randint
import arrow
import os
import requests
import zipfile
import shutil

class UserState(StatesGroup):
	crystal_popol = State()
	promocodename = State()

async def start(message: types.Message):
	if not message.chat.username:
		await message.answer("Для пользования ботом установите username в настройках телеграма.")
	elif not Users.select().where(Users.user_id == message.chat.id).exists():
		date = arrow.utcnow().format('YYYY-MM-DD')
		Users.create(user_id=message.chat.id, username=message.chat.username, date=date)
		for _ in range(1):
			if len(message.text.split()) == 1:
				break
			ref = message.text.split()[1]
			if not ref.isdigit():
				break
			ref = int(ref)
			if not Users.select().where(Users.user_id == ref).exists():
				break
			refInfo = Users.select().where(Users.user_id == ref)[0]
			Users.update(ref_id=ref).where(Users.user_id == message.chat.id).execute()
			try:
				await bot.send_message(ref, f"@{message.chat.username} присоединился по вашей рефералке. Вы будете получать 1% с его пополнений.")
			except:
				pass
		await message.answer("Добро пожаловать.", reply_markup=menuUser)
	else:
		userInfo = Users.select().where(Users.user_id == message.chat.id)[0]
		if userInfo.blocked:
			return await message.answer("Вы заблокированы.")
		Users.update(username=message.chat.username).where(Users.user_id == message.chat.id).execute()
		await message.answer("Добро пожаловать.", reply_markup=menuUser)

async def handler(message: types.Message):
	if not Users.select().where(Users.user_id == message.chat.id).exists():
		return await message.answer("Напиши /start.")
	userInfo = Users.select().where(Users.user_id == message.chat.id)[0]
	if userInfo.blocked:
		return await message.answer("Вы заблокированы.")
	if message.text == '👤 Профиль':
		await message.answer(f'👤Личный кабинет, <b>{message.chat.username}</b>:\n\n💾Логин в БД: <code>@{userInfo.username}</code>\n🦫Ваш ID: <code>{userInfo.user_id}</code>\n📆Дата вступления: <code>{userInfo.date}</code>\n\n💸Баланс: <code>{userInfo.balance} RUB</code>\n💎Количество покупок: <code>{userInfo.buy}</code>', reply_markup=profile_menu, parse_mode='html')

	elif message.text == '🎈 Купить':
		await message.answer('Просмотр разделов:', reply_markup=kategoryes)

@dp.callback_query_handler(lambda c: c.data == 'ref_system')
async def ref_system(call: types.CallbackQuery):
	await call.message.delete()
	me = await bot.get_me()
	await call.message.answer(f'Ваша реферальная ссылка:\n<code>http://t.me/{me.username}?start={call.message.chat.id}</code>\n\nЗа каждого реферала вы будете получать 1% с его пополнений', parse_mode='html', reply_markup=menuUser)

@dp.callback_query_handler(lambda c: c.data == 'kategoryes_menu')
async def kategoryes_menu(call: types.CallbackQuery):
	await call.message.delete()
	alls = InlineKeyboardMarkup()
	for razdelss in Razdels.select():
		files = os.listdir(path=f"./logs/{razdelss.name}/")
		alls.add(
			InlineKeyboardButton(text=f'{razdelss.name} | Остаток: {len(files)} | Цена: {razdelss.price}', callback_data=f'razdel_{razdelss.name}')
		)
	alls.add(
		InlineKeyboardButton(text="Назад", callback_data="back_startrazdel")
	)
	await call.message.answer('Просмотр товара:', reply_markup=alls)

@dp.callback_query_handler(lambda c: 'razdel_' in c.data)
async def razdels(call: types.CallbackQuery):
	name = call.data.split('razdel_')[1]
	razdelInfo = Razdels.select().where(Razdels.name == name)[0]
	broninfo = Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name)
	if broninfo.exists():
		dadayf = InlineKeyboardMarkup(row_width=2)
		dadayf.add(
			InlineKeyboardButton(text="Купить 1", callback_data=f"buy_1/{name}"),
			InlineKeyboardButton(text="Купить 2", callback_data=f"buy_2/{name}"),
			InlineKeyboardButton(text="Купить 5", callback_data=f"buy_5/{name}"),
			InlineKeyboardButton(text="Купить 10", callback_data=f"buy_10/{name}"),
			InlineKeyboardButton(text="Назад", callback_data="back_ketegory"),
		)
		files = os.listdir(path=f"./logs/{name}/")
		await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
									text=f'Просмотр категории <b>{name}</b>\n➖➖➖➖➖➖➖➖➖➖\nОписание товара: <code>{razdelInfo.description}</code>\n\nЦена товара: <code>{razdelInfo.price} RUB</code>\nОстаток товара: <code>{len(files)}</code>\n➖➖➖➖➖➖➖➖➖➖',
									reply_markup=dadayf, parse_mode='html')
	else:
		await call.message.delete()
		await call.message.answer('Нет доступного товара', reply_markup=menuUser)

@dp.callback_query_handler(lambda c: 'buy_' in c.data)
async def buys_(call: types.CallbackQuery):
	await call.message.delete()
	type = call.data.split('_')[1].split('/')[0]
	namerazdel = call.data.split('/')[1]
	if type == '1':
		userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
		for razdelInfo in Razdels.select().where(Razdels.name == namerazdel):
			if userInfo.balance < int(razdelInfo.price):
				return await call.message.answer('У вас недостаточно средств.', reply_markup=menuUser)
			else:
				broninfo = Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name)[0]
				keeks = InlineKeyboardMarkup(row_width=2)
				keeks.add(
					InlineKeyboardButton(text="Подтвердить", callback_data=f"accept_1/{namerazdel}"),
					InlineKeyboardButton(text="Отмена", callback_data=f"leavee_1/{namerazdel}")
				)
				alltovars = len(Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name))
				if alltovars >= 1:
					Tovars.update(brony=True, user_id=call.message.chat.id).where(Tovars.name == broninfo.name).where(Tovars.razdel == namerazdel).execute()
					await call.message.answer(f'Вы забронировали товар!\n\nВы собираетесь купить товар: {namerazdel}\n➖➖➖➖➖➖➖➖➖➖\nОписание товара: {razdelInfo.description}\n\nЦена товара: {razdelInfo.price}\n➖➖➖➖➖➖➖➖➖➖\n\nПодтвердите покупку 1 товаров на общую сумму {razdelInfo.price}', reply_markup=keeks)
					Users.update(balance=userInfo.balance - int(razdelInfo.price)).where(Users.user_id == call.message.chat.id).execute()
				else:
					return await call.message.answer('В этом разделе нет столько логов.')
	elif type == '2':
		userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
		for razdelInfo in Razdels.select().where(Razdels.name == namerazdel):
			if userInfo.balance < int(razdelInfo.price) * 2:
				return await call.message.answer('У вас недостаточно средств.', reply_markup=menuUser)
			else:
				keeks = InlineKeyboardMarkup(row_width=2)
				keeks.add(
					InlineKeyboardButton(text="Подтвердить", callback_data=f"accept_2/{namerazdel}"),
					InlineKeyboardButton(text="Отмена", callback_data=f"leavee_2/{namerazdel}")
				)
				alltovars = len(Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name))
				if alltovars >= 2:
					for i in range(2):
						broninfo = Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name)[0]
						Tovars.update(brony=True, user_id=call.message.chat.id).where(Tovars.name == broninfo.name).where(Tovars.razdel == namerazdel).execute()
					await call.message.answer(f'Вы забронировали товар!\n\nВы собираетесь купить товар: {namerazdel}\n➖➖➖➖➖➖➖➖➖➖\nОписание товара: {razdelInfo.description}\n\nЦена товара: {razdelInfo.price}\n➖➖➖➖➖➖➖➖➖➖\n\nПодтвердите покупку 2 товаров на общую сумму {int(razdelInfo.price) * 2}', reply_markup=keeks)
					Users.update(balance=userInfo.balance - int(razdelInfo.price)*2).where(Users.user_id == call.message.chat.id).execute()
				else:
					return await call.message.answer('В этом разделе нет столько логов.')
	elif type == '5':
		userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
		for razdelInfo in Razdels.select().where(Razdels.name == namerazdel):
			if userInfo.balance < int(razdelInfo.price) * 2:
				return await call.message.answer('У вас недостаточно средств.', reply_markup=menuUser)
			else:
				keeks = InlineKeyboardMarkup(row_width=2)
				keeks.add(
					InlineKeyboardButton(text="Подтвердить", callback_data=f"accept_5/{namerazdel}"),
					InlineKeyboardButton(text="Отмена", callback_data=f"leavee_5/{namerazdel}")
				)
				alltovars = len(Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name))
				if alltovars >= 5:
					for i in range(5):
						broninfo = Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name)[0]
						Tovars.update(brony=True, user_id=call.message.chat.id).where(Tovars.name == broninfo.name).where(Tovars.razdel == namerazdel).execute()
					await call.message.answer(f'Вы забронировали товар!\n\nВы собираетесь купить товар: {namerazdel}\n➖➖➖➖➖➖➖➖➖➖\nОписание товара: {razdelInfo.description}\n\nЦена товара: {razdelInfo.price}\n➖➖➖➖➖➖➖➖➖➖\n\nПодтвердите покупку 5 товаров на общую сумму {int(razdelInfo.price) * 5}', reply_markup=keeks)
					Users.update(balance=userInfo.balance - int(razdelInfo.price)*5).where(Users.user_id == call.message.chat.id).execute()
				else:
					return await call.message.answer('В этом разделе нет столько логов.')
	elif type == '10':
		userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
		for razdelInfo in Razdels.select().where(Razdels.name == namerazdel):
			if userInfo.balance < int(razdelInfo.price) * 10:
				return await call.message.answer('У вас недостаточно средств.', reply_markup=menuUser)
			else:
				keeks = InlineKeyboardMarkup(row_width=2)
				keeks.add(
					InlineKeyboardButton(text="Подтвердить", callback_data=f"accept_10/{namerazdel}"),
					InlineKeyboardButton(text="Отмена", callback_data=f"leavee_10/{namerazdel}")
				)
				alltovars = len(Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name))
				if alltovars >= 5:
					for i in range(10):
						broninfo = Tovars.select().where(Tovars.brony == False).where(Tovars.razdel == razdelInfo.name)[1]
						Tovars.update(brony=True, user_id=call.message.chat.id).where(Tovars.name == broninfo.name).where(Tovars.razdel == namerazdel).execute()
					await call.message.answer(f'Вы забронировали товар!\n\nВы собираетесь купить товар: {namerazdel}\n➖➖➖➖➖➖➖➖➖➖\nОписание товара: {razdelInfo.description}\n\nЦена товара: {razdelInfo.price}\n➖➖➖➖➖➖➖➖➖➖\n\nПодтвердите покупку 10 товаров на общую сумму {int(razdelInfo.price) * 10}', reply_markup=keeks)
					Users.update(balance=userInfo.balance - int(razdelInfo.price) * 10).where(Users.user_id == call.message.chat.id).execute()
				else:
					return await call.message.answer('В этом разделе нет столько логов.')

@dp.callback_query_handler(lambda c: 'leavee_' in c.data)
async def leavee(call: types.CallbackQuery):
	await call.message.delete()
	type = call.data.split('_')[1].split('/')[0]
	userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
	razdelInfo = Razdels.select().where(Razdels.price)[0]
	broninfo = Tovars.select().where(Tovars.user_id == call.message.chat.id)[0]
	if type == '1':
		Tovars.update(brony=False, user_id=0).where(Tovars.name == broninfo.name).where(Tovars.user_id == call.message.chat.id).execute()
		Users.update(balance=userInfo.balance + int(razdelInfo.price)).where(Users.user_id == call.message.chat.id).execute()
		await call.message.answer('Бронь отменена', reply_markup=menuUser)
	elif type == '2':
		for i in range(2):
			broninfo = Tovars.select().where(Tovars.user_id == call.message.chat.id)[0]
			Tovars.update(brony=False, user_id=0).where(Tovars.name == broninfo.name).where(Tovars.user_id == call.message.chat.id).execute()
		Users.update(balance=userInfo.balance + int(razdelInfo.price)*2).where(Users.user_id == call.message.chat.id).execute()
		await call.message.answer('Бронь отменена', reply_markup=menuUser)
	elif type == '5':
		for i in range(5):
			broninfo = Tovars.select().where(Tovars.user_id == call.message.chat.id)[0]
			Tovars.update(brony=False, user_id=0).where(Tovars.name == broninfo.name).where(Tovars.user_id == call.message.chat.id).execute()
		Users.update(balance=userInfo.balance + int(razdelInfo.price)*5).where(Users.user_id == call.message.chat.id).execute()
		await call.message.answer('Бронь отменена', reply_markup=menuUser)
	elif type == '10':
		for i in range(10):
			broninfo = Tovars.select().where(Tovars.user_id == call.message.chat.id)[0]
			Tovars.update(brony=False, user_id=0).where(Tovars.name == broninfo.name).where(Tovars.user_id == call.message.chat.id).execute()
		Users.update(balance=userInfo.balance + int(razdelInfo.price)*10).where(Users.user_id == call.message.chat.id).execute()
		await call.message.answer('Бронь отменена', reply_markup=menuUser)

@dp.callback_query_handler(lambda c: 'accept_' in c.data)
async def accept_(call: types.CallbackQuery):
	await call.message.delete()
	type = call.data.split('_')[1].split('/')[0]
	namerazdel = call.data.split('/')[1]
	userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
	razdelInfo = Razdels.select().where(Razdels.price)[0]
	broninfo = Tovars.select().where(Tovars.user_id == call.message.chat.id)[0]
	logs = os.listdir(f"./logs/{namerazdel}/")
	if type == '1':
		os.replace(f"./logs/{namerazdel}/{broninfo.name}.zip", f"{broninfo.name}.zip")
		z = zipfile.ZipFile(f'./rent/{call.message.chat.username}.zip', 'w')
		z.write(f'{broninfo.name}.zip')
		z.close()
		await bot.send_document(call.message.chat.id, open(f'./rent/{call.message.chat.username}.zip', 'rb'))
		Users.update(buy=Users.buy+1).where(Users.user_id == call.message.chat.id).execute()
		broninfo.delete_instance()
		os.remove(f"./{broninfo.name}.zip")
		os.remove(f"./rent/{call.message.chat.username}.zip")
	elif type == '2':
		os.mkdir(f"./rent/{call.message.chat.username}")
		for test in Tovars.select().where(Tovars.user_id == call.message.chat.id):
			os.replace(f"./logs/{namerazdel}/{test.name}.zip", f"./rent/{call.message.chat.username}/{test.name}.zip")
			z = zipfile.ZipFile(f'./rent/{call.message.chat.username}.zip', 'w')
			path = f"./rent/{call.message.chat.username}"
			for root, dirs, files in os.walk(path):
				for file in files:
					z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))
			test.delete_instance()
			z.close()
		await bot.send_document(call.message.chat.id, open(f'./rent/{call.message.chat.username}.zip', 'rb'))
		Users.update(buy=Users.buy+2).where(Users.user_id == call.message.chat.id).execute()
		shutil.rmtree(f'./rent/{call.message.chat.username}')
		os.remove(f"./rent/{call.message.chat.username}.zip")
	elif type == '5':
		os.mkdir(f"./rent/{call.message.chat.username}")
		for test in Tovars.select().where(Tovars.user_id == call.message.chat.id):
			os.replace(f"./logs/{namerazdel}/{test.name}.zip", f"./rent/{call.message.chat.username}/{test.name}.zip")
			z = zipfile.ZipFile(f'./rent/{call.message.chat.username}.zip', 'w')
			path = f"./rent/{call.message.chat.username}"
			for root, dirs, files in os.walk(path):
				for file in files:
					z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))
			test.delete_instance()
			z.close()
		await bot.send_document(call.message.chat.id, open(f'./rent/{call.message.chat.username}.zip', 'rb'))
		Users.update(buy=Users.buy+5).where(Users.user_id == call.message.chat.id).execute()
		shutil.rmtree(f'./rent/{call.message.chat.username}')
		os.remove(f"./rent/{call.message.chat.username}.zip")
	elif type == '10':
		os.mkdir(f"./rent/{call.message.chat.username}")
		for test in Tovars.select().where(Tovars.user_id == call.message.chat.id):
			os.replace(f"./logs/{namerazdel}/{test.name}.zip", f"./rent/{call.message.chat.username}/{test.name}.zip")
			z = zipfile.ZipFile(f'./rent/{call.message.chat.username}.zip', 'w')
			path = f"./rent/{call.message.chat.username}"
			for root, dirs, files in os.walk(path):
				for file in files:
					z.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))
			test.delete_instance()
			z.close()
		await bot.send_document(call.message.chat.id, open(f'./rent/{call.message.chat.username}.zip', 'rb'))
		Users.update(buy=Users.buy+10).where(Users.user_id == call.message.chat.id).execute()
		shutil.rmtree(f'./rent/{call.message.chat.username}')
		os.remove(f"./rent/{call.message.chat.username}.zip")

@dp.callback_query_handler(lambda c: c.data == 'popolnenie')
async def popolnenie(call: types.CallbackQuery):
	await call.message.delete()
	await call.message.answer('Выберите способ пополнения:', reply_markup=payments)

@dp.callback_query_handler(lambda c: 'payment' in c.data)
async def payment(call: types.CallbackQuery):
	type = call.data.split('_')[1]
	if type == 'crystal':
		await call.message.delete()
		await call.message.answer('Введите сумму пополнения в рублях:', reply_markup=back_)
		await UserState.crystal_popol.set()

@dp.message_handler(state=UserState.crystal_popol)
async def crystal_popol(message: types.Message, state: FSMContext):
	if message.text.isdigit():
		data = {
			'auth_login': f'{kassa}',
			'auth_secret': f'{api}',
			'amount': f'{message.text}',
			'type': 'topup',
			'lifetime': 60
		}
		r = requests.post('https://api.crystalpay.io/v2/invoice/create/', json=data).json()
		id_c = r['id']
		menu = types.InlineKeyboardMarkup()
		menu.add(
			types.InlineKeyboardButton(text="Перейти к оплате", url=r['url'])
		).add(
			types.InlineKeyboardButton(text="✅Проверить оплату", callback_data=f"CRYSTcheck{id_c}/{message.text}")
		)
		await message.answer(f'🧾Создали счёт. Не забудь нажать на кнопку сразу после оплаты!\n⏱Время на оплату: 60 минут!\n\n📨Способ пополнения: 💎CrystalPay\n💰Сумма: {message.text} руб.', reply_markup=menu)
		await state.reset_state(with_data=False)
	else:
		await message.answer("Введите цифры, пожалуйста.")

@dp.callback_query_handler(lambda c: 'CRYSTcheck' in c.data)
async def check(call: types.CallbackQuery):
	id = call.data.split('CRYSTcheck')[-1].split("/")[0]
	amount = call.data.split('CRYSTcheck')[-1].split("/")[1]
	data = {
		'auth_login': f'{kassa}',
		'auth_secret': f'{api}',
		'id': f'{id}'
	}
	r = requests.post('https://api.crystalpay.io/v2/invoice/info/', json=data).json()
	if r["state"] == "payed":
		userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
		ref = userInfo.ref_id
		Users.update(balance=userInfo.balance + int(amount)).where(Users.user_id == call.message.chat.id).execute()
		if ref:
			refInfo = Users.select().where(Users.user_id == ref)[0]
			Users.update(balance=refInfo.balance + round(int(amount) / 100, 2)).where(Users.user_id == ref).execute()
			try:
				await bot.send_message(ref, f"Вам начислено {round(int(amount) / 100, 2)} рублей с реферала @{userInfo.username}.")
			except:
				pass
		await call.message.delete()
		await call.message.answer(f"<code>На ваш баланс пополнено {amount} рублей.</code>", reply_markup=menuUser,
								  parse_mode='html')
		await call.bot.send_message(log_chat, f"@{call.message.chat.username} Пополнил счёт на {amount} рублей🔔")
	else:
		await call.answer('Оплата не найдена.', show_alert=True)

@dp.callback_query_handler(lambda c: c.data == 'back_main', state="*")
async def back_main(call: types.CallbackQuery, state: FSMContext):
	await call.message.delete()
	await state.finish()
	userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
	if userInfo.blocked:
		return await call.message.answer("Вы заблокированы.")
	else:
		await call.message.answer(f'👤Личный кабинет, <b>{call.message.chat.username}</b>:\n\n💾Логин в БД: <code>@{userInfo.username}</code>\n🦫Ваш ID: <code>{userInfo.user_id}</code>\n📆Дата вступления: <code>{userInfo.date}</code>\n\n💸Баланс: <code>{userInfo.balance} RUB</code>\n💎Количество покупок: <code>{userInfo.buy}</code>', reply_markup=profile_menu, parse_mode='html')

@dp.callback_query_handler(lambda c: c.data == 'back_promocode', state="*")
async def back_main(call: types.CallbackQuery, state: FSMContext):
	await call.message.delete()
	await state.finish()
	userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
	if userInfo.blocked:
		return await call.message.answer("Вы заблокированы.")
	else:
		await call.message.answer(f'👤Личный кабинет, <b>{call.message.chat.username}</b>:\n\n💾Логин в БД: <code>@{userInfo.username}</code>\n🦫Ваш ID: <code>{userInfo.user_id}</code>\n📆Дата вступления: <code>{userInfo.date}</code>\n\n💸Баланс: <code>{userInfo.balance} RUB</code>\n💎Количество покупок: <code>{userInfo.buy}</code>', reply_markup=profile_menu, parse_mode='html')

@dp.callback_query_handler(lambda c: 'back' in c.data)
async def back(call: types.CallbackQuery, state: FSMContext):
	type = call.data.split('_')[1]
	if type =='profile':
		await call.message.delete()
		userInfo = Users.select().where(Users.user_id == call.message.chat.id)[0]
		if userInfo.blocked:
			return await call.message.answer("Вы заблокированы.")
		else:
			await call.message.answer(f'👤Личный кабинет, <b>{call.message.chat.username}</b>:\n\n💾Логин в БД: <code>@{userInfo.username}</code>\n🦫Ваш ID: <code>{userInfo.user_id}</code>\n📆Дата вступления: <code>{userInfo.date}</code>\n\n💸Баланс: <code>{userInfo.balance} RUB</code>\n💎Количество покупок: <code>{userInfo.buy}</code>', reply_markup=profile_menu, parse_mode='html')
	elif type == 'startrazdel':
		await call.message.delete()
		await call.message.answer('Просмотр разделов:', reply_markup=kategoryes)
	elif type == 'ketegory':
		alls = InlineKeyboardMarkup()
		for razdelss in Razdels.select():
			files = os.listdir(path=f"./logs/{razdelss.name}/")
			alls.add(
				InlineKeyboardButton(text=f'{razdelss.name} | Остаток: {len(files)} | Цена: {razdelss.price}', callback_data=f'razdel_{razdelss.name}')
			)
		alls.add(
			InlineKeyboardButton(text='Назад', callback_data='back_startrazdel')
		)
		await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Просмотр разделов:', reply_markup=alls)

@dp.callback_query_handler(lambda c: c.data == 'promocode')
async def promocode(call: types.CallbackQuery):
	await call.message.delete()
	await call.message.answer('Введите промокод:', reply_markup=back_promo)
	await UserState.promocodename.set()

@dp.message_handler(state=UserState.promocodename)
async def promocode2(message: types.Message, state: FSMContext):
	if not Promocode.select().where(Promocode.name == message.text).exists():
		await message.answer('Нету такого промокода.')
		await state.reset_state(with_data=False)
	else:
		userInfo = Users.select().where(Users.user_id == message.chat.id)[0]
		if userInfo.used == True:
			await message.answer('Вы уже использовали этот промокод.')
			await state.reset_state(with_data=False)
		else:
			promoInfo = Promocode.select().where(Promocode.name == message.text)[0]
			if promoInfo.used > promoInfo.quantity or promoInfo.used == promoInfo.quantity:
				await message.answer('Ты опоздал(')
				promoInfo.delete_instance()
				Users.update(used=False).where(Users.user_id).execute()
				await state.reset_state(with_data=False)
			else:
				promoInfo = Promocode.select().where(Promocode.name == message.text)[0]
				userInfo = Users.select().where(Users.user_id == message.chat.id)[0]
				Users.update(balance=userInfo.balance+int(promoInfo.amount), used=True).where(Users.user_id == message.chat.id).execute()
				Promocode.update(used=promoInfo.used+1).where(Promocode.name == message.text).execute()
				await message.answer('Успешно!', reply_markup=menuUser)
				await state.reset_state(with_data=False)

def register_handlers_user(dp: Dispatcher):
	dp.register_message_handler(start, commands=['start'])
	dp.register_message_handler(handler)