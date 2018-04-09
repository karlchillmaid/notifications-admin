import json
from datetime import timedelta

TTL = timedelta(hours=24).total_seconds()


def _make_key(prefix, args, key_from_args):

    if key_from_args is None:
        key_from_args = [0]

    return '-'.join(
        [prefix] + [args[index] for index in key_from_args]
    )


def set(prefix, key_from_args=None):

    def _set(client_method):

        def new_client_method(client_instance, *args, **kwargs):
            redis_key = _make_key(prefix, args, key_from_args)
            cached = client_instance.redis_client.get(redis_key)
            if cached:
                return json.loads(cached.decode('utf-8'))
            api_response = client_method(client_instance, *args, **kwargs)
            client_instance.redis_client.set(
                redis_key,
                json.dumps(api_response),
                ex=TTL
            )
            return api_response

        return new_client_method
    return _set


def expire(prefix, key_from_args=None):

    def _expire(client_method):

        def new_client_method(client_instance, *args, **kwargs):
            redis_key = _make_key(prefix, args, key_from_args)
            client_instance.redis_client.expire(redis_key, 0)
            return client_method(client_instance, *args, **kwargs)

        return new_client_method

    return _expire
