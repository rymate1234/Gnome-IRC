__author__ = 'ryan'
class UserList(object):
    def __init__(self):
        self.users = []
        self.raw_users = []

    def add_users(self, users):
        self.users.extend(users)
        for user in users:
            user = user.replace("@", "").replace("+", "")
            self.raw_users.append(user)

    def has_user(self, user):
        if user in self.raw_users:
            return True
        return False

    def get_users(self):
        return self.users

    def get_raw_users(self):
        return self.raw_users

    def change_user(self, old_nick, new_nick):
        # totally optimal honest
        user_prefix = ""
        for user in self.users:
            if old_nick in user:
                user_prefix = user[0]
                self.users.remove(user)
        self.raw_users.remove(old_nick)

        self.add_user(user_prefix + new_nick)

    def remove_user(self, nick):
        # totally optimal honest
        for user in self.users:
            if nick in user:
                self.users.remove(user)
        self.raw_users.remove(nick)

    def __iter__(self):
        for elem in self.users:
            yield elem

    def add_user(self, nick):
        self.users.append(nick)
        user = nick.replace("@", "").replace("+", "")
        self.raw_users.append(user)