next_id = 1  # Biến toàn cục (Global)

def create_student():
    # Không có dòng "global next_id"
    global next_id
    next_id += 1  # DÒNG NÀY GÂY SẬP SERVER
    return next_id

create_student()
print(next_id)