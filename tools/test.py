import win32print
for p in win32print.EnumPrinters(
    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
):
    print(p[2])
