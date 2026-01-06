"""Test Mesa 3.x Agent initialization."""

from mesa.agent import Agent

class TestAgent(Agent):
    def __init__(self, model, unique_id):
        # Mesa 3.4.0 bug workaround - don't call super()
        self.model = model
        self.unique_id = unique_id
        self.test = True

# Test
try:
    ta = TestAgent(None, 123)
    print(f"✅ Success! unique_id = {ta.unique_id}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

