from __init__ import create_app

app = create_app()

if __name__ == '__main__':
    print("アクセスURL: http://localhost:5003/general/explamation")
    app.run(debug=True, port=5003)
