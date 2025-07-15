from src import create_app

app = create_app()

if __name__ == "__main__":
    # running on 5001 to avoid conflicts
    app.run(host="127.0.0.1", port=5001, debug=True)
