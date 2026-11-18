USERS = {
    1: {
        "f": "Văn",
        "l": "Nguyễn",
        "first_name": "Văn",
        "last_name": "Nguyễn",
        "email": "a@vnu.vn",
    },
    2: {
        "f": "Trang",
        "l": "Trần",
        "first_name": "Trang",
        "last_name": "Trần",
        "email": "b@vnu.vn",
    },
}


def get_user(uid):
    return USERS.get(uid)
