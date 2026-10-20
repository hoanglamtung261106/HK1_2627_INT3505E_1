import sys
from pathlib import Path

# Thêm thư mục exercise_2 vào sys.path để pytest luôn import được models, routes, pagination
exercise_dir = Path(__file__).resolve().parent
if str(exercise_dir) not in sys.path:
    sys.path.insert(0, str(exercise_dir))
