from helpers import _create_friendship_pair, _find_friend_conversation_route

from app.utils.jwt_utils import create_access_token


def test_list_friends_empty_by_default(client, user_factory):
    user = user_factory("nofriends@example.com", "nofriends")
    token = create_access_token({"sub": str(user.id)})

    client.cookies.set("access_token", token)
    response = client.get("/api/v1/friends")

    assert response.status_code == 200
    assert response.json() == []

def test_list_friends_returns_friend_items(client, user_factory, event_loop):
    me = user_factory("me@example.com", "me")
    friend = user_factory("friend@example.com", "friend")

    _create_friendship_pair(me.id, friend.id, event_loop)

    token = create_access_token({"sub": str(me.id)})
    client.cookies.set("access_token", token)

    response = client.get("/api/v1/friends")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    item = data[0]
    assert "friend" in item
    assert "isOnline" in item
    assert "lastReadMessageId" in item
    assert "unreadCount" in item

    friend_data = item["friend"]
    assert friend_data["id"] == str(friend.id)
    assert friend_data["email"] == "friend@example.com"
    assert friend_data["username"] == "friend"

def test_open_or_create_conversation_creates_when_missing(client, user_factory, event_loop):
    """
    POST /api/v1/friends/{friend_id}/conversation should create a new DM
    when none exists and return it.
    """
    me = user_factory("me2@example.com", "me2")
    friend = user_factory("friend2@example.com", "friend2")

    _create_friendship_pair(me.id, friend.id, event_loop)

    token = create_access_token({"sub": str(me.id)})
    client.cookies.set("access_token", token)

    path_template, method = _find_friend_conversation_route()
    url = path_template.replace("{friend_id}", str(friend.id))
    response = client.request(method, url)

    assert response.status_code == 200
    conv = response.json()
    assert "id" in conv
    if "isGroup" in conv:
        assert conv["isGroup"] is False
    assert "members" in conv
    assert len(conv["members"]) >= 2

def test_open_or_create_conversation_reuses_existing(client, user_factory, event_loop):
    """
    Calling POST /api/v1/friends/{friend_id}/conversation twice should reuse
    the same conversation (same id).
    """
    me = user_factory("me3@example.com", "me3")
    friend = user_factory("friend3@example.com", "friend3")

    _create_friendship_pair(me.id, friend.id, event_loop)

    token = create_access_token({"sub": str(me.id)})
    client.cookies.set("access_token", token)

    path_template, method = _find_friend_conversation_route()
    url = path_template.replace("{friend_id}", str(friend.id))

    r1 = client.request(method, url)
    r2 = client.request(method, url)

    assert r1.status_code == 200
    assert r2.status_code == 200

    conv1 = r1.json()
    conv2 = r2.json()

    assert conv1["id"] == conv2["id"]

def test_open_or_create_conversation_for_non_friend_forbidden(client, user_factory):
    """
    When the target user is not a friend, the endpoint should return 403.
    """
    me = user_factory("me4@example.com", "me4")
    stranger = user_factory("stranger@example.com", "stranger")

    token = create_access_token({"sub": str(me.id)})
    client.cookies.set("access_token", token)

    path_template, method = _find_friend_conversation_route()
    url = path_template.replace("{friend_id}", str(stranger.id))
    response = client.request(method, url)

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not friends with this user"