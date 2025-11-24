# backend/main.py

from agents.graph import run_graph

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ("exit", "quit"):
            break
        print("🤖:", run_graph(user_input))
