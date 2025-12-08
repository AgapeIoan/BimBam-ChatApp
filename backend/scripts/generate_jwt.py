import os
import uuid

import jwt


def main():
    secret = os.getenv("AUTH__JWT_SECRET_KEY", "change_me")
    algo = os.getenv("AUTH__JWT_ALGORITHM", "HS256")

    users = ["user_a", "user_b"]
    for name in users:
        user_id = uuid.uuid4()
        token = jwt.encode({"sub": str(user_id)}, secret, algorithm=algo)
        print(f"{name} id: {user_id}")
        print(f"{name} token: {token}\n")


if __name__ == "__main__":
    main()
