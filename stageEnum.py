from enum import Enum

class StageEnum:
    none = 0
    waitingForPhoneNumber = 1
    waitingForCode = 2
    waitingForAuthCode = 3
    final = 4
    finalWithAuth = 5