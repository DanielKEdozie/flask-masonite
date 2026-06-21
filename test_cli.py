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
    
    import os
    import shutil
    
    original_cwd = os.getcwd()
    temp_dir = Path(original_cwd) / 'temp_test_run'
    temp_dir.mkdir(exist_ok=True)
    os.chdir(temp_dir)
    
    try:
        from flask_masonite.cli import create_app_structure
        create_app_structure('my_test_app', with_storage=True, with_payment=True)
        
        # Verify files were created directly inside CWD
        assert (temp_dir / 'run.py').exists(), "run.py was not created in CWD"
        assert (temp_dir / 'requirements.txt').exists(), "requirements.txt was not created in CWD"
        assert (temp_dir / 'my_test_app').exists(), "my_test_app folder was not created in CWD"
        assert (temp_dir / 'my_test_app' / 'extensions.py').exists(), "extensions.py was not created"
        assert (temp_dir / 'my_test_app' / 'routes' / '__init__.py').exists(), "routes/__init__.py was not created"
        
        # Verify prebuilt libraries were NOT copied
        assert not (temp_dir / 'libs').exists(), "libs directory should not be created in project root"
        assert not (temp_dir / 'my_test_app' / 'libs').exists(), "libs directory should not be created in app folder"
        
        # Verify Git URL requirements in requirements.txt
        reqs_content = (temp_dir / 'requirements.txt').read_text()
        assert 'git+https://github.com/DanielKEdozie/flask-user.git' in reqs_content, "flask-user Git URL not found in requirements.txt"
        assert 'git+https://github.com/DanielKEdozie/flask-storage.git' in reqs_content, "flask-storage Git URL not found in requirements.txt"
        assert 'git+https://github.com/DanielKEdozie/flask-payment.git' in reqs_content, "flask-payment Git URL not found in requirements.txt"
        
        # Verify the generated code compiles successfully
        import py_compile
        for py_file in (temp_dir / 'my_test_app').glob('**/*.py'):
            py_compile.compile(str(py_file), doraise=True)
        py_compile.compile(str(temp_dir / 'run.py'), doraise=True)
        print("OK: Compilation test passed: all generated files are syntactically valid!")
        print("OK: All assertions passed: structure is correct!")
        
    finally:
        # Restore original state
        builtins.input = original_input
        os.chdir(original_cwd)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_create_app()