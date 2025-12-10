def safe_print(msg):
    try:
        print(msg)
    except Exception as e:
        print(f"Error printing message: {e}")