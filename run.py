from app import create_app

# ✅ Create the Flask app instance using your factory pattern
app = create_app()

# ✅ Optional: Add Flask shell context for easier debugging
@app.shell_context_processor
def make_shell_context():
    from app.extensions import db
    from app.models import User, Client, CapexRequest
    return {
        "db": db,
        "User": User,
        "Client": Client,
        "CapexRequest": CapexRequest
    }

# ✅ Optional: Add custom CLI commands (e.g., seed, health check) here if needed
