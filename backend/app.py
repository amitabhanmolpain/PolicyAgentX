from  flask import Flask,request,jsonify
from graph.policy_graph  import graph 

app = Flask(__name__)

@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.json

    policy_text = data.get("text")

    result = graph.invoke({
        "policy_text": policy_text
    })


    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)