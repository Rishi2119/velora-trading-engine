import MetaTrader5 as mt5

PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

print("Trying to initialize MT5...")
connected = mt5.initialize(PATH)

print("Initialize:", connected)
print("Last error:", mt5.last_error())

if connected:
    print("Terminal info:")
    print(mt5.terminal_info())
