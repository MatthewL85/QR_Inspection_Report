"""Route package marker.

Blueprints are registered centrally in app.create_app(). Keep this package
initializer free of route imports so importing app.routes has no side effects.
"""
