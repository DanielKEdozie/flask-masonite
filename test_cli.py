import sys
from pathlib import Path

# Add the current directory to the path so we can import the CLI
sys.path.insert(0, str(Path(__file__).parent))

# Mock user input to simulate the CLI interaction
class MockInput:
    def __init__(self, inputs):
        self.inputs = inputs
        self.index = 0
        
    def __call__(self, prompt=""):
        if self.index < len(self.inputs):
            response = self.inputs[self.index]
            self.index += 1
            print(prompt + response)  # Print the prompt and response for visibility
            return response
        else:
            return ""

# Replace the input function temporarily
original_input = input

def test_create_app():
    # Define the inputs to simulate user responses
    inputs = ["My Test App", "This is a test application"]
    
    # Create a mock input function
    mock_input = MockInput(inputs)
    
    # Temporarily replace input
    import builtins
    builtins.input = mock_input
    
    try:
        from flask_masonite.cli import create_app_structure
        create_app_structure('my_test_app')
    finally:
        # Restore the original input function
        builtins.input = original_input

if __name__ == "__main__":
    test_create_app()