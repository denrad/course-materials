text = "Привет"
print(text)
print("Длина:", len(text))
print("Байтов UTF-8:", len(text.encode("utf-8")))
print("Ошибочное чтение:", text.encode("utf-8").decode("cp1251"))
