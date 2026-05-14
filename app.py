import json
import logging
import waitress
import os

from flask import Flask, jsonify, request

from geo import get_distance, get_geo_info

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

sessionStorage = {}

def handler(event, context):
    logging.info("Request: %r", event)

    response = {
        "session": event["session"],
        "version": event["version"],
        "response": {"end_session": False},
    }

    handle_dialog(response, event)

    logging.info("Request: %r", response)

    return response


def handle_dialog(res, req):
    user_id = req["session"]["user_id"]

    if req["session"]["new"]:
        res["response"]["text"] = "Привет! Назови своё имя!"
        sessionStorage[user_id]["first_name"] = None
        sessionStorage[user_id]["game_started"] = False
        sessionStorage[user_id]["guessed_cities"] = []
        return

    if sessionStorage[user_id]["first_name"] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res["response"]["text"] = "Не расслышала имя. Повтори, пожалуйста!"
        else:
            sessionStorage[user_id]["first_name"] = first_name
            if "guessed_cities" not in sessionStorage[user_id]:
                sessionStorage[user_id]["guessed_cities"] = []
            res["response"]["text"] = (
                f"Приятно познакомиться, {first_name.title()}. Я Алиса.\n"
                f"Я могу сказать в какой стране город или сказать расстояние между городами!"
            )
            res["response"]["buttons"] = [
                {"title": "Да", "hide": True},
                {"title": "Нет", "hide": True},
            ]
        return

    cities = get_cities(req)
    name = sessionStorage[user_id]["first_name"]

    if len(cities) == 0:
        res["response"]["text"] = (
            f"{name.title()}, ты не написал название не одного города!"
        )

    elif len(cities) == 1:
        res["response"]["text"] = "Этот город в стране - " + get_geo_info(
            cities[0], "country"
        )

    elif len(cities) == 2:
        distance = get_distance(
            get_geo_info(cities[0], "coordinates"),
            get_geo_info(cities[1], "coordinates"),
        )
        res["response"]["text"] = (
            "Расстояние между этими городами: " + str(round(distance)) + " км."
        )

    else:
        res["response"]["text"] = f"{name.title()}, слишком много городов!"


def get_cities(req):
    cities = []

    for entity in req["request"]["nlu"]["entities"]:
        if entity["type"] == "YANDEX.GEO":
            if "city" in entity["value"].keys():
                cities.append(entity["value"]["city"])

    return cities


def get_first_name(req):
    for entity in req["request"]["nlu"]["entities"]:
        if entity["type"] == "YANDEX.FIO":
            return entity["value"].get("first_name", None)
    return None


@app.route("/")
def health():
    return ""


@app.route("/post", methods=["POST"])
def main():
    logging.info("Request: %r", request.json)
    response = {
        "session": request.json["session"],
        "version": request.json["version"],
        "response": {"end_session": False},
    }
    handle_dialog(response, request.json)
    logging.info("Request: %r", response)
    return jsonify(response)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    waitress.serve(app, host="0.0.0.0", port=port)
