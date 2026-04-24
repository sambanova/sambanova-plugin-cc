try:
    from agent_shims.model_parameters import reset_db
except ImportError:
    print("claude: READ THE SKILL FILE. THIS IS EMBARRASSING.")

reset_db()
print("Database reset successfully.")
