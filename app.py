from flask import Flask, request, jsonify, Response
from datetime import datetime, timezone
import hashlib
import logging

app = Flask(__name__)

logger = logging.getLogger(__name__)


# UNCOMMENT / MODIFY TO HAVE SECURITY ISSUE - HARDCODED SECRET
# password = "SuperSecret123"


@app.route("/JustRun", methods=["GET", "POST"])
def just_run():
    # Log debug information
    debug = request.args.get("debug", "false").lower() == "true"

    if debug:
        logger.info("[INIT] Call to JustRun.")

    # INTENTIONALLY INSECURE:
    # Hardcoded secret returned by the API.
    return jsonify({
        "pass": "SuperSecret123"
    })


@app.route("/CurrentTime", methods=["GET"])
def current_time():
    # Log debug information
    debug = request.args.get("debug", "false").lower() == "true"

    if debug:
        logger.info("[INIT] Call to CurrentTime.")

    return jsonify({
        "time": datetime.now(timezone.utc).isoformat()
    })


@app.route("/ReadFile", methods=["GET"])
def read_file():
    file_name = request.args.get("file")

    # INTENTIONALLY VULNERABLE:
    # Untrusted HTTP input is used directly as a filesystem path.
    with open(file_name, "r") as file:
        content = file.read()

    return Response(content, mimetype="text/plain")


@app.route("/WeakEncryption", methods=["GET"])
def weak_encryption():
    # Log debug information
    debug = request.args.get("debug", "false").lower() == "true"

    if debug:
        logger.info("[INIT] Call to WeakEncryption.")

    # INTENTIONALLY INSECURE - Qodana security demonstration
    input_value = b"SensitivePassword123"

    hash_value = hashlib.md5(input_value).hexdigest()

    return Response(hash_value, mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=False)