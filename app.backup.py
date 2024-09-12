from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "API is working!"

@app.route('/generate_results', methods=['POST'])
def generate_results():
    data = request.json
    league_id = data.get('league_id')
    week = data.get('week')

    if not league_id or not week:
        return jsonify({"error": "Invalid input. 'league_id' and 'week' are required."}), 400

    # Replace this with your logic to get matchups
    results = [f"League ID: {league_id}, Week: {week}"] 
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
