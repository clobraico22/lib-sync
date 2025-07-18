import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import aiohttp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Authentication with Spotify
# auth_manager = SpotifyClientCredentials(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET')
auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)


# Function to fetch data (example: artist information)
def fetch_artist_info(artist_id):
    print("AAA")
    return sp.track(artist_id)


# List of artist IDs you want to fetch information for
artist_ids = [
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
    "40EsdChhIP1ZT9RYOcfUI0",
    "0H6wjgFfHI7vf5SaX2T14n",
    "05tmGPn4fFdVpnsMt0YW5S",
    "2GjC0P8uCItsOxEYXtm7kv",
    "7jZM5w05mGhw6wTB1okhD9",
    "3yDIp0kaq9EFKe07X1X2rz",
    "0Xf8oDAJYd2D0k3NLI19OV",
    "5Q81rlcTFh3k6DQJXPdsot",
    "5P8FHUS4EuE2FXskLnqkAg",
    "10GT4yz8c6xjjnPGtGPI1l",
    "2oSihaE9ObkcZVx2LAxySj",
    "2YEnrpAWWaNRFumgde1lLH",
    "78ECvrY5jP8mbGU52iyNSw",
    "0vSfjPjAbekoehCpmy1RV1",
    "2WBJQGf1bT1kxuoqziH5g4",
    "28yVvEvA2lT3K5RNIhV1Dj",
    "7LvvNoUPwTZpgXDWBRrfHg",
    "4aKZ8rfdsQeR7YSskFu9V3",
    "6GGVr7WgIWhsnJNdGyPklP",
    "4wrzxtBZw20ufDstKyTnnP",
    "380fnmlGnkyueBMqGWx2k5",
    "0IhfJZiFjHqE9mJ9INjp7x",
    "0cmWgDlu9CwTgxPhf403hb",
    "1tRBmMtER4fGrzrt8O9VpS",
    "6z9EDgWh3ZJZKIJI5Q71Cq",
    "5kLzaeSHrmS7okc5XNE6lv",
    "2D9Oe8R9UhbMvFAsMJpXj0",
    "3p4rWxMeVAsWCHG8F0HyRj",
    "2nhdOVEJpiDFkwcaBxpWCP",
    "4rzWjR3L3M54c6I25NzdM3",
    "36TuJoh0o1hF6TsZIggHH0",
    "0PavAVTZWBEpaj4iJdKCyj",
    "0Sz2jslaxjcw2VM5zYh2jK",
    "1GVbOnrND8b3eh2JZ4opw8",
    "0BlAuudg3BELkqP2nONKSW",
    "4csQIMQm6vI2A2SCVDuM2z",
    "7mGI9Sd66FqHjIkwzkgbG7",
    "0IF46mUS8NXjgHabxk2MCM",
    "6PTNNcLg90Kkl89JcEwKhT",
    "1H1sDUWSlytzifZTDpKgUA",
    "2AR42Ur9PcchQDtEdwkv4L",
    "0rTh1tAdrEbdKZBTiiAQSo",
    "0HHa7ZJZxUQlg5l2mB0N0f",
    "4lBSzo2LS8asEzoePv6VLM",
    "2hk94pAZS1iYSqoICeTyh1",
    "4xfA60YoR4UbBxuOn9WXJq",
    "5FgLkieOqGXPn01dnbJp9Z",
    "2w7IutHv5g4e8LumrwtjWR",
    "2XOvFG8pp1XAV1V6ZJABim",
    "24JRvbKfTcF2x7c2kCCJrW",
    "41vv2Tj1knysv6MuFUmdwi",
    "20O4Ik25BbWfWBz0kZtsxX",
    "2CKaDZ1Yo8YnWega9IeUzB",
    "2iT8KIetokMHRjhj8dJuNn",
    "1uF7AFfGahplhiaHEy9NNl",
    "2mLA48B366zkELXYx7hcDN",
    "3SGhL82phnYh9XBuSp0Wew",
    "34ehU42UfPtkgHMoD9gMJD",
    "0vUJ3QLN3MlRfjOc2LjGWp",
    "17dbJyUCrxh4I7iyUrjaHU",
    "4sf3QZW8a3xZ14IGsOAzoy",
    "5nI09GHOrlMO2wJNfDm2OD",
    "6wbsiIvg0rsbL9JlLAH9GA",
]  # Replace with actual artist IDs


artist_ids = [
    "0XRU3hfrxwicmk4wRkqs8B",
    "3csPCeXsj2wezyvkRFzvmV",
    "5zbQoW1WWTzvITE8w4ckoC",
    "2IDtMW47SEAptw9RwNREm0",
    "6TILJrqby5UzMV1EemkxtN",
    "7mC3RkNNTV6p2j9w4F8Ip4",
]

start_time = time.time()

# Use ThreadPoolExecutor to parallelize requests
with ThreadPoolExecutor(max_workers=20) as executor:
    # Submit all the tasks and collect the futures
    futures = [executor.submit(fetch_artist_info, artist_id) for artist_id in artist_ids]

    # As each future completes, process its result
    for future in as_completed(futures):
        artist_info = future.result()
        print(artist_info)  # Or process the result in any other way you need

end_time = time.time()


async def fetch_artist_info_2(session, artist_id):
    auth_manager = SpotifyClientCredentials(
        client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET"
    )
    token_info = auth_manager.get_access_token(as_dict=False)

    headers = {"Authorization": f"Bearer {token_info}"}
    url = f"https://api.spotify.com/v1/artists/{artist_id}"

    async with session.get(url, headers=headers) as response:
        return await response.json()


async def main(artist_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_artist_info_2(session, artist_id) for artist_id in artist_ids]
        artist_infos = await asyncio.gather(*tasks)
        for artist_info in artist_infos:
            print(artist_info)


start_time_asyncio = time.time()

asyncio.run(main(artist_ids))

end_time_asyncio = time.time()

print(f"total runtime threads: {(end_time - start_time):.3f} seconds")
print(f"total runtime asyncio: {(end_time_asyncio - start_time_asyncio):.3f} seconds")

# asyncio much faster
