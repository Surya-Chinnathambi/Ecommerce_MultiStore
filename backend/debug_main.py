import traceback
try:
    import app.main
except Exception as e:
    with open('start_error.txt', 'w') as f:
        traceback.print_exc(file=f)
