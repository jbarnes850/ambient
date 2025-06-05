"""Test OpenAI package to see available modules"""
import openai

print("OpenAI version:", openai.__version__)
print("\nAvailable attributes:")
for attr in dir(openai):
    if not attr.startswith('_'):
        print(f"  - {attr}")

# Check for agents-related functionality
try:
    from openai import Agent
    print("\nAgent class found!")
except ImportError:
    print("\nNo Agent class in openai package")

# Check for beta features
try:
    import openai.beta
    print("\nBeta module found:")
    for attr in dir(openai.beta):
        if not attr.startswith('_'):
            print(f"  - beta.{attr}")
except:
    print("\nNo beta module")