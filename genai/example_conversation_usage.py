#!/usr/bin/env python3
"""
Example Usage: Question Answering with Conversation Context

This script demonstrates how to use the conversation context feature
of the GenAI service for maintaining context across questions.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

import httpx

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "octocat"
WEEK = "2024-W03"


async def ask_question(client: httpx.AsyncClient, question: str, conversation_id: Optional[str] = None) -> dict:
    """Ask a question with optional conversation context"""
    
    payload = {
        "question": question,
        "context": {
            "focus_areas": [],
            "include_evidence": True,
            "reasoning_depth": "detailed",
            "max_evidence_items": 5,
            "max_conversation_history": 5
        }
    }
    
    # Add conversation ID if provided
    if conversation_id:
        payload["context"]["conversation_id"] = conversation_id
    
    response = await client.post(
        f"{BASE_URL}/users/{USERNAME}/weeks/{WEEK}/questions",
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


async def get_conversation(client: httpx.AsyncClient, conversation_id: str) -> Optional[dict]:
    """Get conversation details by ID"""
    response = await client.get(f"{BASE_URL}/conversations/{conversation_id}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting conversation: {response.status_code} - {response.text}")
        return None


async def demonstration():
    """Demonstrate conversation context in action"""
    
    print("🤖 GenAI Conversation Context Demo")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Question 1: Initial question (creates new conversation)
        print("\n📝 Question 1: What did I work on this week?")
        response1 = await ask_question(client, "What did I work on this week?")
        
        if not response1:
            print("Failed to get response for first question")
            return
        
        conversation_id = response1.get("conversation_id")
        print(f"💬 Started conversation: {conversation_id}")
        print(f"🎯 Answer: {response1['answer'][:200]}...")
        print(f"🔍 Confidence: {response1['confidence']}")
        
        # Question 2: Follow-up question with context
        print("\n📝 Question 2: What were the main challenges I faced?")
        response2 = await ask_question(
            client, 
            "What were the main challenges I faced?", 
            conversation_id=conversation_id
        )
        
        if response2:
            print(f"🎯 Answer: {response2['answer'][:200]}...")
            print(f"🔍 Confidence: {response2['confidence']}")
            print("✨ This answer should reference the previous conversation!")
        
        # Question 3: Another follow-up
        print("\n📝 Question 3: How can I improve based on this week's work?")
        response3 = await ask_question(
            client, 
            "How can I improve based on this week's work?", 
            conversation_id=conversation_id
        )
        
        if response3:
            print(f"🎯 Answer: {response3['answer'][:200]}...")
            print(f"🔍 Confidence: {response3['confidence']}")
        
        # Show full conversation
        print("\n📋 Full Conversation Thread:")
        print("-" * 30)
        conversation = await get_conversation(client, conversation_id)
        
        if conversation:
            print(f"Conversation ID: {conversation['conversation_id']}")
            print(f"User: {conversation['user']}")
            print(f"Week: {conversation['week']}")
            print(f"Created: {conversation['created_at']}")
            print(f"Total turns: {len(conversation['turns'])}")
            
            for i, turn in enumerate(conversation['turns'], 1):
                print(f"\n  Turn {i}:")
                print(f"    Q: {turn['question']}")
                print(f"    A: {turn['answer'][:100]}...")
                print(f"    Confidence: {turn['confidence']}")
                print(f"    Asked at: {turn['asked_at']}")


async def comparative_demo():
    """Show the difference between with and without conversation context"""
    
    print("\n🔄 Comparative Demo: With vs Without Context")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Without context (separate conversations)
        print("\n🚫 WITHOUT Conversation Context:")
        print("-" * 40)
        
        response1 = await ask_question(client, "What did I work on this week?")
        if response1:
            print(f"Q1: What did I work on this week?")
            print(f"A1: {response1['answer'][:150]}...")
        
        # This creates a NEW conversation (no context)
        response2 = await ask_question(client, "What challenges did I face?")
        if response2:
            print(f"\nQ2: What challenges did I face?")
            print(f"A2: {response2['answer'][:150]}...")
            print("❌ This answer won't reference the previous question")
        
        # With context (same conversation)
        print("\n✅ WITH Conversation Context:")
        print("-" * 40)
        
        response3 = await ask_question(client, "What did I accomplish this week?")
        if response3:
            conversation_id = response3.get("conversation_id")
            print(f"Q1: What did I accomplish this week?")
            print(f"A1: {response3['answer'][:150]}...")
        
        # This continues the same conversation (with context)
        response4 = await ask_question(
            client, 
            "What challenges did I face?", 
            conversation_id=conversation_id
        )
        if response4:
            print(f"\nQ2: What challenges did I face?")
            print(f"A2: {response4['answer'][:150]}...")
            print("✅ This answer can reference the previous question and answer!")


if __name__ == "__main__":
    print("Starting GenAI Conversation Context demonstration...")
    print("Make sure the GenAI service is running on localhost:8000")
    print(f"And that user '{USERNAME}' has contributions for week '{WEEK}'")
    
    choice = input("\nChoose demo:\n1. Basic conversation demo\n2. Comparative demo\n3. Both\nChoice (1-3): ")
    
    if choice == "1":
        asyncio.run(demonstration())
    elif choice == "2":
        asyncio.run(comparative_demo())
    elif choice == "3":
        asyncio.run(demonstration())
        asyncio.run(comparative_demo())
    else:
        print("Invalid choice. Running basic demo...")
        asyncio.run(demonstration()) 