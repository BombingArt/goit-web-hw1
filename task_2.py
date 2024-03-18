import pickle
from collections import UserDict
from datetime import datetime
from abc import ABC, abstractmethod

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Контакт не знайдено"
        except IndexError:
            return "Вкажіть аргумент для команди"
    return inner

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __str__(self):
        return f"І'мя: {self.value}"

class Phone(Field):
    def __init__(self, phone):
        if not self.validate_phone(phone):
            raise ValueError("Неправильний формат номеру. Введіть 10 цифр")
        super().__init__(phone)

    def validate_phone(self, phone):
        return len(phone) == 10 and phone.isdigit()

    def __str__(self):
        return f"{self.value}"

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Неправильний формат дати. Використовуйте ДД.ММ.РРРР")

    def __str__(self):
        return f"Дата народження: {self.value.strftime('%d.%m.%Y')}"

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        found = False
        for p in self.phones:
            if p.value == old_phone:
                found = True
                if p.validate_phone(new_phone):
                    p.value = new_phone
                else:
                    raise ValueError("Новий номер недійсний. Спробуйте ще раз")
        if not found:
            raise ValueError("Номер не знайдено")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Контакт: {self.name}, Телефони: {' '.join(str(p)+', ' for p in self.phones)} {self.birthday if self.birthday else ''}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            return self.data.pop(name)

    def get_upcoming_birthdays(self):
        upcoming_birthdays = []
        today_date = datetime.today().date()

        for record in self.data.values():
            if record.birthday:
                birthday_date = record.birthday.value.date()

                next_birthday = birthday_date.replace(year=today_date.year)

                if next_birthday < today_date:
                    next_birthday = next_birthday.replace(year=today_date.year + 1)

                if (next_birthday - today_date).days <= 7:
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": next_birthday.strftime("%d.%m.%Y")
                    })

        return upcoming_birthdays

@input_error
def add_contact(book, args):
    if len(args) != 2:
        raise ValueError("Для додавання контакту введіть ім'я та номер телефону у форматі: add <ім'я> <телефон>")
    name, phone = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return "Контакт додано"

@input_error
def change_contact(book, args):
    if len(args) != 3:
        raise ValueError("Для зміни контакту вкажіть ім'я, поточний та новий номер телефону у форматі: change <ім'я> <старий телефон> <новий телефон>")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is not None:
        record.edit_phone(old_phone, new_phone)
        return "Номер змінено"
    else:
        return "Контакт не знайдено"

@input_error
def show_phone(book, args):
    if not args:
        raise ValueError("Вкажіть ім'я для перегляду номера телефону у форматі: phone <ім'я>")
    name = " ".join(args)
    record = book.find(name)
    if record is not None:
        phones = [str(phone) for phone in record.phones]
        if phones:
            return ", ".join(phones)
        else:
            return "Немає номерів для цього контакту"
    else:
        return "Контакт не знайдено"

@input_error
def remove_phone(book, args):
    if len(args) != 2:
        raise ValueError("Вкажіть ім'я контакту та номер для видалення у форматі: remove-phone <ім'я> <номер>")
    name, phone = args
    record = book.find(name)
    if record is not None:
        record.remove_phone(phone)
        return "Номер видалено"
    else:
        return "Контакт не знайдено"

@input_error
def add_birthday(book, args):
    if len(args) != 2:
        raise ValueError("Вкажіть ім'я та дату народження у форматі: add-birthday <ім'я> <дата народження>")
    name, birthday = args
    record = book.find(name)
    if record is not None:
        record.add_birthday(birthday)
        return "Дату народження додано"
    else:
        return "Контакт не знайдено"

@input_error
def show_birthday(book, args):
    if not args:
        raise ValueError("Вкажіть ім'я для перегляду дати народження у форматі: show-birthday <ім'я>")
    name = args[0]
    record = book.find(name)
    if record is not None and record.birthday is not None:
        return str(record.birthday)
    else:
        return "Дату народження не знайдено"

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class UserInterface(ABC):
    @abstractmethod
    def show_commands_info(self):
        pass

    @abstractmethod
    def get_user_input(self):
        pass

class ConsoleUserInterface(UserInterface):
    def show_commands_info(self):
        print("Доступні команди:")
        print("hello - Привітальне повідомлення")
        print("add - Додати новий контакт або номер телефону (формат: add <ім'я> <телефон>)")
        print("change - Змінити номер телефону для контакту (формат: change <ім'я> <старий телефон> <новий телефон>)")
        print("phone - Показати номери телефонів для контакту (формат: phone <ім'я>)")
        print("remove-phone - Видалити номер телефону для контакту (формат: remove-phone <ім'я> <телефон>)")
        print("add-birthday - Додати дату народження для контакту (формат: add-birthday <ім'я> <дата народження>)")
        print("show-birthday - Показати дату народження для контакту (формат: show-birthday <ім'я>)")
        print("all - Показати всі контакти")
        print("birthdays - Показати дні народження цього тиждня")
        print("exit, close - Вийти з програми\n")


    def get_user_input(self):
        return input("Введіть команду: ")

def main():
    ui = ConsoleUserInterface()
    book = load_data()

    print("\nПомічник вітає Вас\n")
    ui.show_commands_info()
    while True:
        user_input = ui.get_user_input()
        command, *args = parse_input(user_input)

        if command == "exit" or command == "close":
            print("До зустрічі!")
            save_data(book)
            break

        elif command == "hello":
            print("Чим можу допомогти?")

        elif command == "add":
            print(add_contact(book, args))

        elif command == "change":
            print(change_contact(book, args))

        elif command == "phone":
            print(show_phone(book, args))

        elif command == "remove-phone":
            print(remove_phone(book, args))

        elif command == "add-birthday":
            print(add_birthday(book, args))

        elif command == "show-birthday":
            print(show_birthday(book, args))
        
        elif command == "all":
            contacts = book.data
            if contacts:
                for contact in contacts.values():
                    print(contact)

        elif command == "birthdays":
            upcoming_birthdays = book.get_upcoming_birthdays()
            if upcoming_birthdays:
                for bday in upcoming_birthdays:
                    print(f"День рождения {bday['name']} - {bday['birthday']}")
            else:
                print("Немає днів народження цього тиждня")

        elif command == "help":
            ui.show_commands_info()

        else:
            print("Неправильна команда. Для списку команд введіть 'help'.")

if __name__ == "__main__":
    main()
