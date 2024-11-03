from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps
import re
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
            if re.fullmatch(r'\d{10}', value):
                super().__init__(value)
            else:
                raise ValueError('Invalid phone number format.')


class Birthday(Field):
    def __init__(self, value):
        try:
            input_date = datetime.strptime(value, '%d.%m.%Y').date()
            super().__init__(input_date)
        except ValueError:
            raise ValueError('Invalid date format. Use DD.MM.YYYY')


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, new_phone):
        for phone in self.phones:
            if phone.value == new_phone:
                return False

        self.phones.append(Phone(new_phone))
        return True

    def edit_phone(self, old_phone, new_phone):
        for i, phone in enumerate(self.phones):
            if phone.value == old_phone:
                self.phones[i] = Phone(new_phone)
                return True
        return False

    def remove_phone(self, phone_to_remove):
        for phone in self.phones:
            if phone.value == phone_to_remove:
                self.phones.remove(phone)
                return True

        print(f'Phone {phone_to_remove} not found.')
        return False

    def find_phone(self, phone_to_find):
        for phone in self.phones:
            if phone.value == phone_to_find:
                return phone.value

        print(f'Phone {phone_to_find} not found.')
        return False
    
    def add_birthday(self, new_birthday):
        if self.birthday:
            return False
        self.birthday = Birthday(new_birthday)
        return True

    def __str__(self):
        phones_str = '; '.join(phone.value for phone in self.phones)
        birthday_str = f', birthday: {self.birthday.value.strftime("%d.%m.%Y")}' if self.birthday else ''
        return f'Contact name: {self.name.value}, phones: {phones_str}{birthday_str}'


class AddressBook(UserDict):
    def add_record(self, new_record):
        if new_record.name.value not in self.data:
            self.data[new_record.name.value] = new_record
            return True
        else:
            print(f'Record for "{new_record.name.value}" already exists.')
            return False

    def find(self, searched_name):
        if searched_name in self.data.keys():
            return self.data[searched_name]
        else:
            return False

    def delete(self, searched_name):
        if searched_name in self.data.keys():
            del self.data[searched_name]
            return True
        else:
            print(f'No record found for "{searched_name}".')
            return False

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        end_date = today + timedelta(days=7)
        upcoming_birthdays = []
    
        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.value
                birthday_this_year = birthday.replace(year = today.year)
                
                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year = today.year + 1)
                
                if today <= birthday_this_year <= end_date:
                    if birthday_this_year.weekday() == 5:
                        congratulation_date = birthday_this_year + timedelta(days=2)
                    elif birthday_this_year.weekday() == 6:
                        congratulation_date = birthday_this_year + timedelta(days=1)
                    else:
                        congratulation_date = birthday_this_year
                    
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime('%d.%m.%Y')
                    })
    
        return upcoming_birthdays


# ____________________________Bot_____________________________


def input_error(handler):
    @wraps(handler)
    def inner(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except KeyError:
            return 'Contact not found. Please enter a valid contact name.'
        except ValueError as e:
            if 'Invalid phone number format.' in str(e):
                return str(e)
            if 'Invalid date format. Use DD.MM.YYYY' in str(e):
                return str(e)
            return 'Please enter the correct number of arguments.'
        except IndexError:
            return 'Incomplete information provided. Please provide all necessary details.'
    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    try:
        new_phone = Phone(phone)
    except ValueError as e:
        return str(e)
    
    record = book.find(name)
    
    if not record:
        record = Record(name)
        book.add_record(record)
        message = 'Contact added.'
    else:
        message = 'Contact updated.'

    if not record.add_phone(phone):
        message = f'The phone number "{phone}" is already associated with this contact.'

    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)

    if not record:
        return f'Contact "{name}" not found in address book.'

    if not record.edit_phone(old_phone, new_phone):
        return f'Phone number "{old_phone}" not found for contact "{name}".'

    return 'Contact updated.'


@input_error
def get_contact_phones(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        return '\n'.join(p.value for p in record.phones)
    else:
        return f'"{name}" is not found in adress book.'


@input_error
def get_all_contacts(book: AddressBook):
    if book.data.items():
        return '\n'.join(str(record) for record in book.data.values())
    else:
        return 'The address book is empty.'


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)

    if not record:
        return f'Contact "{name}" not found in address book.'
    
    if not record.add_birthday(birthday):
        return 'The birthday has already been set.'
    
    return 'Birthday is set.'


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)

    if not record:
        return f'Contact "{name}" not found in address book.'
    
    if not record.birthday:
        return f'Birthday is not set for contact "{name}"'
    
    return record.birthday.value.strftime('%d.%m.%Y')


@input_error
def birthdays(book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays in the next 7 days."
    else:
        result = "Upcoming birthdays:\n"
        for birthday in upcoming_birthdays:
            result += f'{birthday["name"]} - {birthday["congratulation_date"]}\n'
        return result.strip()


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    book = load_data()
    print('Welcome to the assistant bot!')
    while True:
        user_input = input('Enter a command: ')

        if not user_input:
            print("Please enter a valid command.")
            continue

        command, *args = parse_input(user_input)
        match command:
            case 'close' | 'exit':
                save_data(book)
                print('Good bye!')
                break
            case 'hello':
                print('How can I help you?')
            case 'add':
                print(add_contact(args, book))
            case 'change':
                print(change_contact(args, book))
            case 'phone':
                print(get_contact_phones(args, book))
            case 'all':
                print(get_all_contacts(book))
            case 'add-birthday':
                print(add_birthday(args, book))
            case 'show-birthday':
                print(show_birthday(args, book))
            case 'birthdays':
                print(birthdays(book))
            case _:
                print('Invalid command.')


if __name__ == '__main__':
    main()