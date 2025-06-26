import getpass
import ctypes


username = getpass.getuser()
print(f"Имя текущей учетной записи: {username}")


def get_full_username():
    GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
    NameDisplay = 3  
    size = ctypes.pointer(ctypes.c_ulong(0))
    GetUserNameEx(NameDisplay, None, size)
    nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
    GetUserNameEx(NameDisplay, nameBuffer, size)
    return nameBuffer.value

print("Полное имя пользователя:", get_full_username())
