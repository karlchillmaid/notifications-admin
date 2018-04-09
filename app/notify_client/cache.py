from datetime import timedelta

TTL = timedelta(hours=24).total_seconds()


def _make_key(prefix, args, key_from_args):

    if key_from_args is None:
        key_from_args = [0]

    return '-'.join(
        [prefix] + [args[index] for index in key_from_args]
    )


def set(prefix, key_from_args=None):

    def _set(fn):

        def new_client_method(api_client, *args, **kwargs):
            redis_key = _make_key(prefix, args, key_from_args)
            cached = api_client.redis_client.get(redis_key)
            if cached:
                return json.loads(cached.decode('utf-8'))
            api_resp = fn(api_client, *args, **kwargs)
            api_client.redis_client.set(
                redis_key,
                json.dumps(api_resp),
                ex=TTL
            )
            return api_resp

        return new_client_method
    return _set


def expire(prefix, key_from_args=None):

    def _expire(fn):

        def new_client_method(api_client, *args, **kwargs):
            redis_key = _make_key(prefix, args, key_from_args)
            api_client.redis_client.expire(redis_key, 0)
            return fn(api_client, *args, **kwargs)

        return new_client_method

    return _expire
