import os
import sys
from dotenv import load_dotenv

load_dotenv()

from rag.groq_client import generate as generate_client
from app.services.groq_service import generate as generate_service

def main():
    print("Testing groq_client.generate...")
    res1 = generate_client("Hello, what is your model name?")
    print("Result 1:", res1)
    
    print("\n--------------------------\n")
    
    print("Testing groq_service.generate...")
    res2 = generate_service("Hello, what is your model name?")
    print("Result 2:", res2)

if __name__ == "__main__":
    main()
