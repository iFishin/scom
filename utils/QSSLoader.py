
class QSSLoader:
    def __init__(self):
        pass

    @staticmethod
    def load_stylesheet(style: str) -> str:
        with open(style, "r", encoding="UTF-8") as file:
            return file.read()
