import asyncio
import functools
import json
from typing import (Any, Callable, Dict, Hashable, List, Optional, Tuple, Type,
                    Union)
from urllib.parse import urlencode

import urllib3

class APIManager:
    key: Optional[str] = None
    pool = urllib3.PoolManager(num_pools=20, maxsize=10, block=False, timeout=30)

    def __init__(self, rapid_api_key: str) -> None:
        self.key = rapid_api_key
        self.internal_cache: Dict[str, Dict[str, Any]] = {}
        # This holds the results of functions that have been called, with their args and kwargs frozen into a str.

    @staticmethod
    def json_decode(desired_key: Hashable = None) -> Callable:
        """
        Decodes a JSON response into a list of strings based on the desired_key.
        :param desired_key: The key to look for in the JSON response.
        :return: A metadecorator that can be wrapped around any function that returns a JSON response.
        """

        def inner_func(func: Callable) -> Any:
            async def wrapper(*args: list, **kwargs: dict) -> List[Any]:
                response = await func(*args, **kwargs)

                if desired_key:
                    results: List[Any] = []

                    def _decode_dict(a_dict: dict) -> dict:
                        try:
                            results.append(a_dict[desired_key])
                        except KeyError:
                            pass
                        return a_dict

                    json.loads(response.data.decode("utf-8"), object_hook=_decode_dict)
                    return results
                else:
                    return json.loads(response.data.decode("utf-8"))

            wrapper.__doc__ = func.__doc__
            wrapper.__name__ = func.__name__

            return wrapper

        return inner_func

    # A decorator that runs synchronous functions in run_in_executor
    @staticmethod
    def run_in_executor(func: Callable) -> Callable:
        """
        Runs a function in an executor.
        :param func: The function to run.
        :return: The wrapped function.
        """

        async def wrapper(*args: list, **kwargs: dict) -> Any:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))

        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__

        return wrapper
    

    def post(self, url: str, host_name: str) -> Callable:
        """
        Decorator that shortens the process of making post requests to RapidAPI.
        :param url: The URL to post to.
        :param host_name: The host name of the RapidAPI.
        :return: A metadecorator that can be wrapped around any function which returns a tuple of (data (str), query_params (dict))."""
        def inner_func(func: Callable) -> Any:
            threaded_pool = urllib3.PoolManager(num_pools=20, maxsize=10, block=False, timeout=30)

            #@self.cache
            @self.run_in_executor
            def wrapper(*args: list, **kwargs: dict) -> Union[str, dict]:
                data, query_params = func(*args, **kwargs)
                headers = {
                    "x-rapidapi-host": host_name,
                    "x-rapidapi-key": self.key,
                    "content-type": "application/json",
                }
                response = threaded_pool.request(
                    "POST", url + urlencode(query_params), headers=headers, body=data
                )
                return response
            wrapper.__doc__ = func.__doc__
            wrapper.__name__ = func.__name__
            return wrapper
        return inner_func


    def get(self, host_name: str) -> Callable:
        """
        Decorator that shortens the process of making get requests to RapidAPI.
        :param host_name: The host name of the RapidAPI.
        :return: A metadecorator that can be wrapped around any function which returns a url string."""

        def inner_func(func: Callable) -> Any:
            threaded_pool = urllib3.PoolManager(num_pools=20, maxsize=10, block=False, timeout=30)
            #@self.cache
            @self.run_in_executor
            def wrapper(*args: list, **kwargs: dict) -> Union[str, dict]:
                url: str = func(*args, **kwargs)
                headers = {
                    "x-rapidapi-host": host_name,
                    "x-rapidapi-key": self.key,
                }
                response = threaded_pool.request("GET", url, headers=headers)
                return response
            wrapper.__doc__ = func.__doc__
            wrapper.__name__ = func.__name__

            return wrapper

        return inner_func

    # Static method that takes a function, extracts its source-code, and turns it from a synchronous post/get using the requests module into a urllib3 request. 