import pytest

from app.api.v1.deps import get_current_user
from app.db import session as session_module
from app.utils.jwt_utils import create_access_token
from tests.fixtures import user_factory


def test_get_current_user_with_real_database(user_factory, event_loop):
    """
    Full integration performed synchronously using the test event loop:
    - create a user via user_factory
    - create a JWT for that user
    - call get_current_user with a real AsyncSession
    """
    email = "integration-auth@example.com"
    username = "integration-user"

    user = user_factory(email, username)
    token = create_access_token({"sub": str(user.id)})

    async def _run():
        async with session_module.AsyncSessionLocal() as session:
            current_user = await get_current_user(acces_token=token, session=session)

        assert current_user.id == user.id
        assert current_user.email == email
        assert current_user.username == username

    event_loop.run_until_complete(_run())
