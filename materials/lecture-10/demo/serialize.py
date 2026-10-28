"""Учебная сериализация: только вымышленные данные."""
import json

order = {"id": 125, "recipient": "Анна"}
message = json.dumps(order, ensure_ascii=False)
print(message)
print(message.encode("utf-8"))
