import pickle


class CartHandler:
    def __init__(self, request):
        self.request = request
        cookie = request.COOKIES.get('cart')
        print(cookie)
        if cookie:
            self.cart = pickle.loads(bytes.fromhex(cookie))
        else:
            self.cart = {}

    def add(self, ids, n):
        self.cart[ids] = n

    def update(self, ids, action, n):
        if action == '-' and n < self.cart[ids]:
            self.cart[ids] -= int(n)
        elif action == '+':
            self.cart[ids] += int(n)

    def remove(self, ids):
        res = self.cart.pop(ids, False)
        print(res)

    def save(self):
        data = pickle.dumps(self.cart).hex()
        return data

    def load(self):
        try:
            cookie = self.request.COOKIES["cart"]
            self.cart = pickle.loads(bytes.fromhex(cookie))
        except Exception as ex:
            self.cart = dict()
            return ex

    def fix(self, query):
        fixed_cart = {}
        for key, item in self.cart.items():
            if int(key) in query:
                fixed_cart[key] = item
        self.cart = fixed_cart

    def clear(self):
        self.cart.clear()

    def __str__(self):
        return self.cart.__str__()

    def __len__(self):
        return self.cart.__len__()
