from main import app

if __name__ == '__main__':
    print("Starting ABC College Admission Portal on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=False)
