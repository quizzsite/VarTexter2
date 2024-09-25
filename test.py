class Text:
    def get(self):
        print("dweofjep")    

class API:
    def __init__(self) -> None:
        self.Text = Text()


a = API()
a.Text.get()