**Problem:** RapidAPI's code snippets for Python look like this:

```python
import requests

url = "https://microsoft-computer-vision3.p.rapidapi.com/analyze"

querystring = {"language":"en","descriptionExclude":"Celebrities","visualFeatures":"ImageType","details":"Celebrities"}

payload = "{
    \"url\": \"http://example.com/images/test.jpg\"
}"
headers = {
    'content-type': "application/json",
    'x-rapidapi-host': "microsoft-computer-vision3.p.rapidapi.com",
    'x-rapidapi-key': "{key}"
    }

response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

print(response.text)
```

* This will essentially freeze your app for two seconds while it waits for a server response.

* There's a lot of extraneous boilerplate in this snippet, and it's bad for maintenance if you're copy-pasting it everywhere.

* No keyword arguments

**Solution:**

```python
from pyrapidapi import to_post

old_code_snippet = "..."

to_post("new_function_name", desired_fields="part of the json response that you want", func_source=old_code_snippet)
```

And magically, you should get a function that looks like this:

```python
@apis.json_decode("text")
@apis.post(
    "https://microsoft-translator-text.p.rapidapi.com/translate?",
    "microsoft-translator-text.p.rapidapi.com",
)
def translate(text: str, to_lang: str) -> Tuple[str, dict]:
    return json.dumps([{"text": text}]), {
        "to": to_lang,
        "api-version": "3.0",
        "includeAlignment": "false",
        "profanityAction": "NoAction",
        "textType": "plain",
    }
```

Another example, for GET requests:
```python
@apis.get("wordsapiv1.p.rapidapi.com")
def info_for_word(info_type: str, word: str) -> str:
    return f"https://wordsapiv1.p.rapidapi.com/words/{word}/{info_type}"
```

Usable via:

```python
from pyrapidapi import APIManager

apis = APIManager("{your key here}")
```

## Installation

```bash
pip install git+https://github.com/ckoshka/pyrapidapi
```